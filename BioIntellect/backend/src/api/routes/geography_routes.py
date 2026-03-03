"""Geography Routes - Complete Geographic Data API."""

from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, List, Any
from src.repositories.geography_repository import GeographyRepository
from src.validators.medical_dto import (
    CountryCreateDTO,
    CountryUpdateDTO,
    RegionCreateDTO,
    RegionUpdateDTO,
    HospitalCreateDTO,
    HospitalUpdateDTO,
    CountryResponseDTO,
    RegionResponseDTO,
    HospitalResponseDTO,
)
from src.security.auth_middleware import (
    get_current_user,
    require_permission,
    Permission,
)
from src.observability.logger import get_logger

logger = get_logger("routes.geography")

router = APIRouter(prefix="/geography", tags=["geography"])

# â”پâ”پâ”پâ”پ COUNTRIES â”پâ”پâ”پâ”پ


@router.get("/countries", response_model=List[CountryResponseDTO])
async def list_countries(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """List all countries with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if is_active is not None:
            filters["is_active"] = is_active

        countries = await repo.list_countries(filters, limit, offset)
        return countries
    except Exception as e:
        logger.error(f"Failed to list countries: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve countries")


@router.get("/countries/{country_id}", response_model=CountryResponseDTO)
async def get_country(
    country_id: str, repo: GeographyRepository = Depends(GeographyRepository)
):
    """Get a specific country by ID."""
    try:
        country = await repo.get_country(country_id)
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
        return country
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get country {country_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve country")


@router.post(
    "/countries",
    response_model=CountryResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_GEOGRAPHY))],
)
async def create_country(
    country_data: CountryCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """Create a new country (Admin/Super Admin only)."""
    try:
        country = await repo.create_country(country_data.dict())
        logger.info(f"Country created by user {user['id']}: {country['id']}")
        return country
    except Exception as e:
        logger.error(f"Failed to create country: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create country")


@router.put(
    "/countries/{country_id}",
    response_model=CountryResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_GEOGRAPHY))],
)
async def update_country(
    country_id: str,
    country_data: CountryUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """Update a country (Admin/Super Admin only)."""
    try:
        country = await repo.update_country(
            country_id, country_data.dict(exclude_unset=True)
        )
        if not country:
            raise HTTPException(status_code=404, detail="Country not found")
        logger.info(f"Country updated by user {user['id']}: {country_id}")
        return country
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update country {country_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update country")


@router.delete(
    "/countries/{country_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_GEOGRAPHY))],
)
async def delete_country(
    country_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """Delete a country (Admin/Super Admin only)."""
    try:
        success = await repo.delete_country(country_id)
        if not success:
            raise HTTPException(status_code=404, detail="Country not found")
        logger.info(f"Country deleted by user {user['id']}: {country_id}")
        return {"success": True, "message": "Country deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete country {country_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete country")


# â”پâ”پâ”پâ”پ REGIONS â”پâ”پâ”پâ”پ


@router.get("/regions", response_model=List[RegionResponseDTO])
async def list_regions(
    country_id: Optional[str] = Query(None, description="Filter by country ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """List all regions with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if country_id:
            filters["country_id"] = country_id
        if is_active is not None:
            filters["is_active"] = is_active

        regions = await repo.list_regions(filters, limit, offset)
        return regions
    except Exception as e:
        logger.error(f"Failed to list regions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve regions")


@router.get("/regions/{region_id}", response_model=RegionResponseDTO)
async def get_region(
    region_id: str, repo: GeographyRepository = Depends(GeographyRepository)
):
    """Get a specific region by ID."""
    try:
        region = await repo.get_region(region_id)
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
        return region
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get region {region_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve region")


@router.post(
    "/regions",
    response_model=RegionResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_GEOGRAPHY))],
)
async def create_region(
    region_data: RegionCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """Create a new region (Admin/Super Admin only)."""
    try:
        region = await repo.create_region(region_data.dict())
        logger.info(f"Region created by user {user['id']}: {region['id']}")
        return region
    except Exception as e:
        logger.error(f"Failed to create region: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create region")


@router.put(
    "/regions/{region_id}",
    response_model=RegionResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_GEOGRAPHY))],
)
async def update_region(
    region_id: str,
    region_data: RegionUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """Update a region (Admin/Super Admin only)."""
    try:
        region = await repo.update_region(
            region_id, region_data.dict(exclude_unset=True)
        )
        if not region:
            raise HTTPException(status_code=404, detail="Region not found")
        logger.info(f"Region updated by user {user['id']}: {region_id}")
        return region
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update region {region_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update region")


@router.delete(
    "/regions/{region_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_GEOGRAPHY))],
)
async def delete_region(
    region_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """Delete a region (Admin/Super Admin only)."""
    try:
        success = await repo.delete_region(region_id)
        if not success:
            raise HTTPException(status_code=404, detail="Region not found")
        logger.info(f"Region deleted by user {user['id']}: {region_id}")
        return {"success": True, "message": "Region deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete region {region_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete region")


# â”پâ”پâ”پâ”پ HOSPITALS â”پâ”پâ”پâ”پ


@router.get("/hospitals", response_model=List[HospitalResponseDTO])
async def list_hospitals(
    region_id: Optional[str] = Query(None, description="Filter by region ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """List all hospitals with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if region_id:
            filters["region_id"] = region_id
        if is_active is not None:
            filters["is_active"] = is_active

        hospitals = await repo.list_hospitals(filters, limit, offset)
        return hospitals
    except Exception as e:
        logger.error(f"Failed to list hospitals: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve hospitals")


@router.get("/hospitals/{hospital_id}", response_model=HospitalResponseDTO)
async def get_hospital(
    hospital_id: str, repo: GeographyRepository = Depends(GeographyRepository)
):
    """Get a specific hospital by ID."""
    try:
        hospital = await repo.get_hospital(hospital_id)
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        return hospital
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get hospital {hospital_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve hospital")


@router.post(
    "/hospitals",
    response_model=HospitalResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_GEOGRAPHY))],
)
async def create_hospital(
    hospital_data: HospitalCreateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """Create a new hospital (Admin/Super Admin only)."""
    try:
        hospital = await repo.create_hospital(hospital_data.dict())
        logger.info(f"Hospital created by user {user['id']}: {hospital['id']}")
        return hospital
    except Exception as e:
        logger.error(f"Failed to create hospital: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create hospital")


@router.put(
    "/hospitals/{hospital_id}",
    response_model=HospitalResponseDTO,
    dependencies=[Depends(require_permission(Permission.MANAGE_GEOGRAPHY))],
)
async def update_hospital(
    hospital_id: str,
    hospital_data: HospitalUpdateDTO,
    user: dict[str, Any] = Depends(get_current_user),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """Update a hospital (Admin/Super Admin only)."""
    try:
        hospital = await repo.update_hospital(
            hospital_id, hospital_data.dict(exclude_unset=True)
        )
        if not hospital:
            raise HTTPException(status_code=404, detail="Hospital not found")
        logger.info(f"Hospital updated by user {user['id']}: {hospital_id}")
        return hospital
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update hospital {hospital_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to update hospital")


@router.delete(
    "/hospitals/{hospital_id}",
    dependencies=[Depends(require_permission(Permission.MANAGE_GEOGRAPHY))],
)
async def delete_hospital(
    hospital_id: str,
    user: dict[str, Any] = Depends(get_current_user),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """Delete a hospital (Admin/Super Admin only)."""
    try:
        success = await repo.delete_hospital(hospital_id)
        if not success:
            raise HTTPException(status_code=404, detail="Hospital not found")
        logger.info(f"Hospital deleted by user {user['id']}: {hospital_id}")
        return {"success": True, "message": "Hospital deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete hospital {hospital_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete hospital")


# â”پâ”پâ”پâ”پ SPECIALTIES â”پâ”پâ”پâ”پ


@router.get("/specialties")
async def list_specialties(
    category: Optional[str] = Query(None, description="Filter by specialty category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(50, le=100, description="Number of results to return"),
    offset: int = Query(0, description="Number of results to skip"),
    repo: GeographyRepository = Depends(GeographyRepository),
):
    """List all medical specialties with optional filtering."""
    try:
        filters: dict[str, Any] = {}
        if category:
            filters["specialty_category"] = category
        if is_active is not None:
            filters["is_active"] = is_active

        specialties = await repo.list_specialties(filters, limit, offset)
        return {"success": True, "data": specialties}
    except Exception as e:
        logger.error(f"Failed to list specialties: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve specialties")

