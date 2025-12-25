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
        const country = countries.find(c => c.country_id === countryId);
        if (!country) return;
        try {
            const regionList = await fetchRegions(country.country_name);
            setRegions(regionList);
        } catch (e) {
            console.error('Failed to load regions', e);
        }
    }, [countries, fetchRegions]);

    // When a region is selected, load its hospitals
    const selectRegion = useCallback(async (regionId) => {
        setSelectedRegionId(regionId);
        setHospitals([]);
        const country = countries.find(c => c.country_id === selectedCountryId);
        const region = regions.find(r => r.region_id === regionId);
        if (!country || !region) return;
        try {
            const hospitalList = await fetchHospitals({
                countryName: country.country_name,
                regionName: region.region_name,
            });
            setHospitals(hospitalList);
        } catch (e) {
            console.error('Failed to load hospitals', e);
        }
    }, [countries, regions, selectedCountryId, fetchHospitals]);

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
