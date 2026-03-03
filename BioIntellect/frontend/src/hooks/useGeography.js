// src/hooks/useGeography.js
// Reusable hook for fetching global geography data (countries, regions, hospitals)
// and handling selections. Used across admin, doctor, patient and signup forms.

import { useState, useEffect, useCallback } from 'react';
import { geographyAPI } from '@/services/api';

export const useGeography = () => {
    const [countries, setCountries] = useState([]);
    const [regions, setRegions] = useState([]);
    const [hospitals, setHospitals] = useState([]);

    const [selectedCountryId, setSelectedCountryId] = useState('');
    const [selectedRegionId, setSelectedRegionId] = useState('');

    // Load countries once on mount
    useEffect(() => {
        const load = async () => {
            try {
                const response = await geographyAPI.getCountries();
                if (response.success) {
                    setCountries(response.data);
                }
            } catch (e) {
                console.error('Failed to load countries', e);
            }
        };
        load();
    }, []);

    // When a country is selected, load its regions
    const selectCountry = useCallback(async (countryId) => {
        setSelectedCountryId(countryId);
        setSelectedRegionId(''); // reset region & hospital
        setRegions([]);
        setHospitals([]);
        if (!countryId) return;

        try {
            const response = await geographyAPI.getRegions(countryId);
            if (response.success) {
                setRegions(response.data);
            }
        } catch (e) {
            console.error('Failed to load regions', e);
        }
    }, []);

    // When a region is selected, load its hospitals
    const selectRegion = useCallback(async (regionId) => {
        setSelectedRegionId(regionId);
        setHospitals([]);
        if (!regionId) return;
        try {
            const response = await geographyAPI.getHospitals(regionId);
            if (response.success) {
                setHospitals(response.data);
            }
        } catch (e) {
            console.error('Failed to load hospitals', e);
        }
    }, []);

    // Helper objects for UI components
    const selectedCountry = countries.find(c => c.country_id === selectedCountryId) || null;
    const selectedRegion = regions.find(r => r.region_id === selectedRegionId) || null;

    /**
     * resolveNames: Standardized helper to convert IDs in a payload to human-readable names.
     */
    const resolveNames = useCallback((formData) => {
        const countryObj = countries.find(c => c.country_id === formData.countryId);
        const regionObj = regions.find(r => r.region_id === formData.regionId);
        const hospitalObj = hospitals.find(h => h.hospital_id === formData.hospitalId);

        return {
            ...formData,
            country: countryObj ? countryObj.country_name : formData.countryId,
            region: regionObj ? regionObj.region_name : formData.regionId,
            hospital_name: hospitalObj ? (hospitalObj.hospital_name || hospitalObj.hospital_name_en) : null
        };
    }, [countries, regions, hospitals]);

    return {
        countries,
        regions,
        hospitals,
        selectedCountry,
        selectedRegion,
        selectCountry,
        selectRegion,
        selectedCountryId,
        selectedRegionId,
        resolveNames
    };
};
