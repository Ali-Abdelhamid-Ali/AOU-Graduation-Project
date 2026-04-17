// src/hooks/useGeography.js
// Reusable hook for fetching global geography data (countries, regions, hospitals)
// and handling selections. Used across admin, doctor, patient and signup forms.

import { useState, useEffect, useCallback, useMemo } from 'react';
import { geographyAPI } from '@/services/api';
import { buildCountryOptions, getStaticRegionsForCountry } from '@/data/world-countries.data';

export const useGeography = () => {
    const [dbCountries, setDbCountries]   = useState([]);
    const [regions,     setRegions]       = useState([]);
    const [hospitals,   setHospitals]     = useState([]);

    const [selectedCountryId, setSelectedCountryId] = useState('');
    const [selectedRegionId,  setSelectedRegionId]  = useState('');

    // Load DB countries once on mount (limit 300 to get all)
    useEffect(() => {
        const load = async () => {
            try {
                const response = await geographyAPI.getCountries(300);
                if (response.success) {
                    setDbCountries(response.data ?? []);
                }
            } catch (e) {
                console.error('Failed to load countries', e);
                // fallback — use world static data only (no DB IDs)
                setDbCountries([]);
            }
        };
        load();
    }, []);

    /**
     * Full country option list: DB records merged with the 250-country world dataset.
     * DB records have priority (they carry real IDs for FK relationships).
     * World records fill every gap so the dropdown always shows all countries.
     */
    const countries = useMemo(() => buildCountryOptions(dbCountries), [dbCountries]);

    // When a country is selected, load its regions (with static fallback)
    const selectCountry = useCallback(async (countryId) => {
        setSelectedCountryId(countryId);
        setSelectedRegionId('');
        setRegions([]);
        setHospitals([]);
        if (!countryId) return;

        try {
            const response = await geographyAPI.getRegions(countryId);
            const dbRegions = (response.success ? response.data : null) ?? [];

            if (dbRegions.length > 0) {
                setRegions(dbRegions);
            } else {
                // No DB regions — build fallback from static world data
                const countryOpt = countries.find(c => c.value === countryId);
                const fallback = countryOpt
                    ? getStaticRegionsForCountry(countryOpt.value, countryOpt.label, countryOpt.code)
                    : [];
                setRegions(fallback);
            }
        } catch (e) {
            console.error('Failed to load regions', e);
            // On error also fallback to static
            const countryOpt = countries.find(c => c.value === countryId);
            const fallback = countryOpt
                ? getStaticRegionsForCountry(countryOpt.value, countryOpt.label, countryOpt.code)
                : [];
            setRegions(fallback);
        }
    }, [countries]);

    // When a region is selected, load its hospitals
    const selectRegion = useCallback(async (regionId) => {
        setSelectedRegionId(regionId);
        setHospitals([]);
        if (!regionId) return;
        try {
            const response = await geographyAPI.getHospitals(regionId);
            if (response.success) {
                setHospitals(response.data ?? []);
            }
        } catch (e) {
            console.error('Failed to load hospitals', e);
        }
    }, []);

    const selectedCountry = useMemo(
        () => countries.find(c => c.value === selectedCountryId) || null,
        [countries, selectedCountryId]
    );
    const selectedRegion = useMemo(
        () => regions.find(r => r.region_id === selectedRegionId) || null,
        [regions, selectedRegionId]
    );

    /**
     * resolveNames: convert IDs in a payload to human-readable names before API submission.
     */
    const resolveNames = useCallback((formData) => {
        const countryOpt = countries.find(c => c.value === formData.countryId);
        const regionObj  = regions.find(r => r.region_id === formData.regionId);
        const hospitalObj = hospitals.find(h => h.hospital_id === formData.hospitalId);

        return {
            ...formData,
            country:       countryOpt  ? countryOpt.label                                          : formData.countryId,
            region:        regionObj   ? regionObj.region_name                                     : formData.regionId,
            hospital_name: hospitalObj ? (hospitalObj.hospital_name || hospitalObj.hospital_name_en) : null,
        };
    }, [countries, regions, hospitals]);

    return {
        countries,          // merged world + DB, SearchableSelect-ready options
        dbCountries,        // raw DB records (for FK lookups)
        regions,
        hospitals,
        selectedCountry,
        selectedRegion,
        selectCountry,
        selectRegion,
        selectedCountryId,
        selectedRegionId,
        resolveNames,
    };
};
