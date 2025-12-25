// src/hooks/useGeography.js
// Reusable hook for fetching global geography data (countries, regions, hospitals)
// and handling selections. Used across admin, doctor, patient and signup forms.

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';

export const useGeography = () => {
    const { fetchCountries, fetchRegions, fetchHospitals } = useAuth();

    const [countries, setCountries] = useState([]);
    const [regions, setRegions] = useState([]);
    const [hospitals, setHospitals] = useState([]);

    const [selectedCountryId, setSelectedCountryId] = useState('');
    const [selectedRegionId, setSelectedRegionId] = useState('');

    // Load countries once on mount
    useEffect(() => {
        const load = async () => {
            try {
                const list = await fetchCountries();
                setCountries(list);
            } catch (e) {
                console.error('Failed to load countries', e);
            }
        };
        load();
    }, [fetchCountries]);

    // When a country is selected, load its regions
    const selectCountry = useCallback(async (countryId) => {
        setSelectedCountryId(countryId);
        setSelectedRegionId(''); // reset region & hospital
        setRegions([]);
        setHospitals([]);
        if (!countryId) return;

        // Resolve country name from ID (ISO code) API requirement
        const countryObj = countries.find(c => c.country_id === countryId);
        const countryName = countryObj ? countryObj.country_name : countryId;

        try {
            const regionList = await fetchRegions(countryName);
            setRegions(regionList);
        } catch (e) {
            console.error('Failed to load regions', e);
        }
    }, [fetchRegions, countries]);

    // When a region is selected, load its hospitals
    const selectRegion = useCallback(async (regionId) => {
        setSelectedRegionId(regionId);
        setHospitals([]);
        if (!regionId) return;
        try {
            const hospitalList = await fetchHospitals(regionId);
            setHospitals(hospitalList);
        } catch (e) {
            console.error('Failed to load hospitals', e);
        }
    }, [fetchHospitals]);

    // Helper objects for UI components
    const selectedCountry = countries.find(c => c.country_id === selectedCountryId) || null;
    const selectedRegion = regions.find(r => r.region_id === selectedRegionId) || null;

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
    };
};
