/**
 * World countries static data — ISO 3166-1 alpha-2 codes, names, regions, and sub-regions.
 * Flags served from flagcdn.com using the 2-letter country code.
 * Used as a fallback / supplement when the backend geography API doesn't have all countries.
 */

/** @typedef {{ code: string, name: string, region: string, subregion: string, flag: string }} WorldCountry */

/** @type {WorldCountry[]} */
export const WORLD_COUNTRIES = [
  { code: 'AF', name: 'Afghanistan',                    region: 'Asia',    subregion: 'Southern Asia' },
  { code: 'AL', name: 'Albania',                        region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'DZ', name: 'Algeria',                        region: 'Africa',  subregion: 'Northern Africa' },
  { code: 'AD', name: 'Andorra',                        region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'AO', name: 'Angola',                         region: 'Africa',  subregion: 'Middle Africa' },
  { code: 'AG', name: 'Antigua and Barbuda',            region: 'Americas',subregion: 'Caribbean' },
  { code: 'AR', name: 'Argentina',                      region: 'Americas',subregion: 'South America' },
  { code: 'AM', name: 'Armenia',                        region: 'Asia',    subregion: 'Western Asia' },
  { code: 'AU', name: 'Australia',                      region: 'Oceania', subregion: 'Australia and New Zealand' },
  { code: 'AT', name: 'Austria',                        region: 'Europe',  subregion: 'Western Europe' },
  { code: 'AZ', name: 'Azerbaijan',                     region: 'Asia',    subregion: 'Western Asia' },
  { code: 'BS', name: 'Bahamas',                        region: 'Americas',subregion: 'Caribbean' },
  { code: 'BH', name: 'Bahrain',                        region: 'Asia',    subregion: 'Western Asia' },
  { code: 'BD', name: 'Bangladesh',                     region: 'Asia',    subregion: 'Southern Asia' },
  { code: 'BB', name: 'Barbados',                       region: 'Americas',subregion: 'Caribbean' },
  { code: 'BY', name: 'Belarus',                        region: 'Europe',  subregion: 'Eastern Europe' },
  { code: 'BE', name: 'Belgium',                        region: 'Europe',  subregion: 'Western Europe' },
  { code: 'BZ', name: 'Belize',                         region: 'Americas',subregion: 'Central America' },
  { code: 'BJ', name: 'Benin',                          region: 'Africa',  subregion: 'Western Africa' },
  { code: 'BT', name: 'Bhutan',                         region: 'Asia',    subregion: 'Southern Asia' },
  { code: 'BO', name: 'Bolivia',                        region: 'Americas',subregion: 'South America' },
  { code: 'BA', name: 'Bosnia and Herzegovina',         region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'BW', name: 'Botswana',                       region: 'Africa',  subregion: 'Southern Africa' },
  { code: 'BR', name: 'Brazil',                         region: 'Americas',subregion: 'South America' },
  { code: 'BN', name: 'Brunei',                         region: 'Asia',    subregion: 'South-Eastern Asia' },
  { code: 'BG', name: 'Bulgaria',                       region: 'Europe',  subregion: 'Eastern Europe' },
  { code: 'BF', name: 'Burkina Faso',                   region: 'Africa',  subregion: 'Western Africa' },
  { code: 'BI', name: 'Burundi',                        region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'CV', name: 'Cabo Verde',                     region: 'Africa',  subregion: 'Western Africa' },
  { code: 'KH', name: 'Cambodia',                       region: 'Asia',    subregion: 'South-Eastern Asia' },
  { code: 'CM', name: 'Cameroon',                       region: 'Africa',  subregion: 'Middle Africa' },
  { code: 'CA', name: 'Canada',                         region: 'Americas',subregion: 'Northern America' },
  { code: 'CF', name: 'Central African Republic',       region: 'Africa',  subregion: 'Middle Africa' },
  { code: 'TD', name: 'Chad',                           region: 'Africa',  subregion: 'Middle Africa' },
  { code: 'CL', name: 'Chile',                          region: 'Americas',subregion: 'South America' },
  { code: 'CN', name: 'China',                          region: 'Asia',    subregion: 'Eastern Asia' },
  { code: 'CO', name: 'Colombia',                       region: 'Americas',subregion: 'South America' },
  { code: 'KM', name: 'Comoros',                        region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'CD', name: 'Congo (DRC)',                    region: 'Africa',  subregion: 'Middle Africa' },
  { code: 'CG', name: 'Congo (Republic)',               region: 'Africa',  subregion: 'Middle Africa' },
  { code: 'CR', name: 'Costa Rica',                     region: 'Americas',subregion: 'Central America' },
  { code: 'CI', name: "Côte d'Ivoire",                  region: 'Africa',  subregion: 'Western Africa' },
  { code: 'HR', name: 'Croatia',                        region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'CU', name: 'Cuba',                           region: 'Americas',subregion: 'Caribbean' },
  { code: 'CY', name: 'Cyprus',                         region: 'Asia',    subregion: 'Western Asia' },
  { code: 'CZ', name: 'Czech Republic',                 region: 'Europe',  subregion: 'Eastern Europe' },
  { code: 'DK', name: 'Denmark',                        region: 'Europe',  subregion: 'Northern Europe' },
  { code: 'DJ', name: 'Djibouti',                       region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'DM', name: 'Dominica',                       region: 'Americas',subregion: 'Caribbean' },
  { code: 'DO', name: 'Dominican Republic',             region: 'Americas',subregion: 'Caribbean' },
  { code: 'EC', name: 'Ecuador',                        region: 'Americas',subregion: 'South America' },
  { code: 'EG', name: 'Egypt',                          region: 'Africa',  subregion: 'Northern Africa' },
  { code: 'SV', name: 'El Salvador',                    region: 'Americas',subregion: 'Central America' },
  { code: 'GQ', name: 'Equatorial Guinea',              region: 'Africa',  subregion: 'Middle Africa' },
  { code: 'ER', name: 'Eritrea',                        region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'EE', name: 'Estonia',                        region: 'Europe',  subregion: 'Northern Europe' },
  { code: 'SZ', name: 'Eswatini',                       region: 'Africa',  subregion: 'Southern Africa' },
  { code: 'ET', name: 'Ethiopia',                       region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'FJ', name: 'Fiji',                           region: 'Oceania', subregion: 'Melanesia' },
  { code: 'FI', name: 'Finland',                        region: 'Europe',  subregion: 'Northern Europe' },
  { code: 'FR', name: 'France',                         region: 'Europe',  subregion: 'Western Europe' },
  { code: 'GA', name: 'Gabon',                          region: 'Africa',  subregion: 'Middle Africa' },
  { code: 'GM', name: 'Gambia',                         region: 'Africa',  subregion: 'Western Africa' },
  { code: 'GE', name: 'Georgia',                        region: 'Asia',    subregion: 'Western Asia' },
  { code: 'DE', name: 'Germany',                        region: 'Europe',  subregion: 'Western Europe' },
  { code: 'GH', name: 'Ghana',                          region: 'Africa',  subregion: 'Western Africa' },
  { code: 'GR', name: 'Greece',                         region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'GD', name: 'Grenada',                        region: 'Americas',subregion: 'Caribbean' },
  { code: 'GT', name: 'Guatemala',                      region: 'Americas',subregion: 'Central America' },
  { code: 'GN', name: 'Guinea',                         region: 'Africa',  subregion: 'Western Africa' },
  { code: 'GW', name: 'Guinea-Bissau',                  region: 'Africa',  subregion: 'Western Africa' },
  { code: 'GY', name: 'Guyana',                         region: 'Americas',subregion: 'South America' },
  { code: 'HT', name: 'Haiti',                          region: 'Americas',subregion: 'Caribbean' },
  { code: 'HN', name: 'Honduras',                       region: 'Americas',subregion: 'Central America' },
  { code: 'HU', name: 'Hungary',                        region: 'Europe',  subregion: 'Eastern Europe' },
  { code: 'IS', name: 'Iceland',                        region: 'Europe',  subregion: 'Northern Europe' },
  { code: 'IN', name: 'India',                          region: 'Asia',    subregion: 'Southern Asia' },
  { code: 'ID', name: 'Indonesia',                      region: 'Asia',    subregion: 'South-Eastern Asia' },
  { code: 'IR', name: 'Iran',                           region: 'Asia',    subregion: 'Southern Asia' },
  { code: 'IQ', name: 'Iraq',                           region: 'Asia',    subregion: 'Western Asia' },
  { code: 'IE', name: 'Ireland',                        region: 'Europe',  subregion: 'Northern Europe' },
  { code: 'IL', name: 'Israel',                         region: 'Asia',    subregion: 'Western Asia' },
  { code: 'IT', name: 'Italy',                          region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'JM', name: 'Jamaica',                        region: 'Americas',subregion: 'Caribbean' },
  { code: 'JP', name: 'Japan',                          region: 'Asia',    subregion: 'Eastern Asia' },
  { code: 'JO', name: 'Jordan',                         region: 'Asia',    subregion: 'Western Asia' },
  { code: 'KZ', name: 'Kazakhstan',                     region: 'Asia',    subregion: 'Central Asia' },
  { code: 'KE', name: 'Kenya',                          region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'KI', name: 'Kiribati',                       region: 'Oceania', subregion: 'Micronesia' },
  { code: 'KW', name: 'Kuwait',                         region: 'Asia',    subregion: 'Western Asia' },
  { code: 'KG', name: 'Kyrgyzstan',                     region: 'Asia',    subregion: 'Central Asia' },
  { code: 'LA', name: 'Laos',                           region: 'Asia',    subregion: 'South-Eastern Asia' },
  { code: 'LV', name: 'Latvia',                         region: 'Europe',  subregion: 'Northern Europe' },
  { code: 'LB', name: 'Lebanon',                        region: 'Asia',    subregion: 'Western Asia' },
  { code: 'LS', name: 'Lesotho',                        region: 'Africa',  subregion: 'Southern Africa' },
  { code: 'LR', name: 'Liberia',                        region: 'Africa',  subregion: 'Western Africa' },
  { code: 'LY', name: 'Libya',                          region: 'Africa',  subregion: 'Northern Africa' },
  { code: 'LI', name: 'Liechtenstein',                  region: 'Europe',  subregion: 'Western Europe' },
  { code: 'LT', name: 'Lithuania',                      region: 'Europe',  subregion: 'Northern Europe' },
  { code: 'LU', name: 'Luxembourg',                     region: 'Europe',  subregion: 'Western Europe' },
  { code: 'MG', name: 'Madagascar',                     region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'MW', name: 'Malawi',                         region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'MY', name: 'Malaysia',                       region: 'Asia',    subregion: 'South-Eastern Asia' },
  { code: 'MV', name: 'Maldives',                       region: 'Asia',    subregion: 'Southern Asia' },
  { code: 'ML', name: 'Mali',                           region: 'Africa',  subregion: 'Western Africa' },
  { code: 'MT', name: 'Malta',                          region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'MH', name: 'Marshall Islands',               region: 'Oceania', subregion: 'Micronesia' },
  { code: 'MR', name: 'Mauritania',                     region: 'Africa',  subregion: 'Western Africa' },
  { code: 'MU', name: 'Mauritius',                      region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'MX', name: 'Mexico',                         region: 'Americas',subregion: 'Central America' },
  { code: 'FM', name: 'Micronesia',                     region: 'Oceania', subregion: 'Micronesia' },
  { code: 'MD', name: 'Moldova',                        region: 'Europe',  subregion: 'Eastern Europe' },
  { code: 'MC', name: 'Monaco',                         region: 'Europe',  subregion: 'Western Europe' },
  { code: 'MN', name: 'Mongolia',                       region: 'Asia',    subregion: 'Eastern Asia' },
  { code: 'ME', name: 'Montenegro',                     region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'MA', name: 'Morocco',                        region: 'Africa',  subregion: 'Northern Africa' },
  { code: 'MZ', name: 'Mozambique',                     region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'MM', name: 'Myanmar',                        region: 'Asia',    subregion: 'South-Eastern Asia' },
  { code: 'NA', name: 'Namibia',                        region: 'Africa',  subregion: 'Southern Africa' },
  { code: 'NR', name: 'Nauru',                          region: 'Oceania', subregion: 'Micronesia' },
  { code: 'NP', name: 'Nepal',                          region: 'Asia',    subregion: 'Southern Asia' },
  { code: 'NL', name: 'Netherlands',                    region: 'Europe',  subregion: 'Western Europe' },
  { code: 'NZ', name: 'New Zealand',                    region: 'Oceania', subregion: 'Australia and New Zealand' },
  { code: 'NI', name: 'Nicaragua',                      region: 'Americas',subregion: 'Central America' },
  { code: 'NE', name: 'Niger',                          region: 'Africa',  subregion: 'Western Africa' },
  { code: 'NG', name: 'Nigeria',                        region: 'Africa',  subregion: 'Western Africa' },
  { code: 'KP', name: 'North Korea',                    region: 'Asia',    subregion: 'Eastern Asia' },
  { code: 'MK', name: 'North Macedonia',                region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'NO', name: 'Norway',                         region: 'Europe',  subregion: 'Northern Europe' },
  { code: 'OM', name: 'Oman',                           region: 'Asia',    subregion: 'Western Asia' },
  { code: 'PK', name: 'Pakistan',                       region: 'Asia',    subregion: 'Southern Asia' },
  { code: 'PW', name: 'Palau',                          region: 'Oceania', subregion: 'Micronesia' },
  { code: 'PA', name: 'Panama',                         region: 'Americas',subregion: 'Central America' },
  { code: 'PG', name: 'Papua New Guinea',               region: 'Oceania', subregion: 'Melanesia' },
  { code: 'PY', name: 'Paraguay',                       region: 'Americas',subregion: 'South America' },
  { code: 'PE', name: 'Peru',                           region: 'Americas',subregion: 'South America' },
  { code: 'PH', name: 'Philippines',                    region: 'Asia',    subregion: 'South-Eastern Asia' },
  { code: 'PL', name: 'Poland',                         region: 'Europe',  subregion: 'Eastern Europe' },
  { code: 'PT', name: 'Portugal',                       region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'QA', name: 'Qatar',                          region: 'Asia',    subregion: 'Western Asia' },
  { code: 'RO', name: 'Romania',                        region: 'Europe',  subregion: 'Eastern Europe' },
  { code: 'RU', name: 'Russia',                         region: 'Europe',  subregion: 'Eastern Europe' },
  { code: 'RW', name: 'Rwanda',                         region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'KN', name: 'Saint Kitts and Nevis',          region: 'Americas',subregion: 'Caribbean' },
  { code: 'LC', name: 'Saint Lucia',                    region: 'Americas',subregion: 'Caribbean' },
  { code: 'VC', name: 'Saint Vincent and the Grenadines',region:'Americas',subregion: 'Caribbean' },
  { code: 'WS', name: 'Samoa',                          region: 'Oceania', subregion: 'Polynesia' },
  { code: 'SM', name: 'San Marino',                     region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'ST', name: 'Sao Tome and Principe',          region: 'Africa',  subregion: 'Middle Africa' },
  { code: 'SA', name: 'Saudi Arabia',                   region: 'Asia',    subregion: 'Western Asia' },
  { code: 'SN', name: 'Senegal',                        region: 'Africa',  subregion: 'Western Africa' },
  { code: 'RS', name: 'Serbia',                         region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'SC', name: 'Seychelles',                     region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'SL', name: 'Sierra Leone',                   region: 'Africa',  subregion: 'Western Africa' },
  { code: 'SG', name: 'Singapore',                      region: 'Asia',    subregion: 'South-Eastern Asia' },
  { code: 'SK', name: 'Slovakia',                       region: 'Europe',  subregion: 'Eastern Europe' },
  { code: 'SI', name: 'Slovenia',                       region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'SB', name: 'Solomon Islands',                region: 'Oceania', subregion: 'Melanesia' },
  { code: 'SO', name: 'Somalia',                        region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'ZA', name: 'South Africa',                   region: 'Africa',  subregion: 'Southern Africa' },
  { code: 'SS', name: 'South Sudan',                    region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'ES', name: 'Spain',                          region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'LK', name: 'Sri Lanka',                      region: 'Asia',    subregion: 'Southern Asia' },
  { code: 'SD', name: 'Sudan',                          region: 'Africa',  subregion: 'Northern Africa' },
  { code: 'SR', name: 'Suriname',                       region: 'Americas',subregion: 'South America' },
  { code: 'SE', name: 'Sweden',                         region: 'Europe',  subregion: 'Northern Europe' },
  { code: 'CH', name: 'Switzerland',                    region: 'Europe',  subregion: 'Western Europe' },
  { code: 'SY', name: 'Syria',                          region: 'Asia',    subregion: 'Western Asia' },
  { code: 'TW', name: 'Taiwan',                         region: 'Asia',    subregion: 'Eastern Asia' },
  { code: 'TJ', name: 'Tajikistan',                     region: 'Asia',    subregion: 'Central Asia' },
  { code: 'TZ', name: 'Tanzania',                       region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'TH', name: 'Thailand',                       region: 'Asia',    subregion: 'South-Eastern Asia' },
  { code: 'TL', name: 'Timor-Leste',                    region: 'Asia',    subregion: 'South-Eastern Asia' },
  { code: 'TG', name: 'Togo',                           region: 'Africa',  subregion: 'Western Africa' },
  { code: 'TO', name: 'Tonga',                          region: 'Oceania', subregion: 'Polynesia' },
  { code: 'TT', name: 'Trinidad and Tobago',            region: 'Americas',subregion: 'Caribbean' },
  { code: 'TN', name: 'Tunisia',                        region: 'Africa',  subregion: 'Northern Africa' },
  { code: 'TR', name: 'Turkey',                         region: 'Asia',    subregion: 'Western Asia' },
  { code: 'TM', name: 'Turkmenistan',                   region: 'Asia',    subregion: 'Central Asia' },
  { code: 'TV', name: 'Tuvalu',                         region: 'Oceania', subregion: 'Polynesia' },
  { code: 'UG', name: 'Uganda',                         region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'UA', name: 'Ukraine',                        region: 'Europe',  subregion: 'Eastern Europe' },
  { code: 'AE', name: 'United Arab Emirates',           region: 'Asia',    subregion: 'Western Asia' },
  { code: 'GB', name: 'United Kingdom',                 region: 'Europe',  subregion: 'Northern Europe' },
  { code: 'US', name: 'United States',                  region: 'Americas',subregion: 'Northern America' },
  { code: 'UY', name: 'Uruguay',                        region: 'Americas',subregion: 'South America' },
  { code: 'UZ', name: 'Uzbekistan',                     region: 'Asia',    subregion: 'Central Asia' },
  { code: 'VU', name: 'Vanuatu',                        region: 'Oceania', subregion: 'Melanesia' },
  { code: 'VE', name: 'Venezuela',                      region: 'Americas',subregion: 'South America' },
  { code: 'VN', name: 'Vietnam',                        region: 'Asia',    subregion: 'South-Eastern Asia' },
  { code: 'YE', name: 'Yemen',                          region: 'Asia',    subregion: 'Western Asia' },
  { code: 'ZM', name: 'Zambia',                         region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'ZW', name: 'Zimbabwe',                       region: 'Africa',  subregion: 'Eastern Africa' },
  { code: 'PS', name: 'Palestine',                      region: 'Asia',    subregion: 'Western Asia' },
  { code: 'XK', name: 'Kosovo',                         region: 'Europe',  subregion: 'Southern Europe' },
  { code: 'TF', name: 'French Southern Territories',    region: 'Africa',  subregion: 'Southern Africa' },
  { code: 'VA', name: 'Vatican City',                   region: 'Europe',  subregion: 'Southern Europe' },
].sort((a, b) => a.name.localeCompare(b.name))

/**
 * Get flag image URL for a country code (2-letter ISO 3166-1 alpha-2).
 * @param {string} code
 * @returns {string}
 */
export function getFlagUrl(code) {
  if (!code) return ''
  return `https://flagcdn.com/w40/${code.toLowerCase()}.png`
}

/**
 * Get all unique world regions from the dataset.
 * @returns {string[]}
 */
export function getWorldRegions() {
  return [...new Set(WORLD_COUNTRIES.map(c => c.region))].sort()
}

/**
 * Get subregions for a given region.
 * @param {string} region
 * @returns {string[]}
 */
export function getSubregions(region) {
  return [...new Set(
    WORLD_COUNTRIES.filter(c => c.region === region).map(c => c.subregion)
  )].sort()
}

/**
 * Build static fallback region options for a country that has no DB regions.
 * Returns the country's own subregion + sibling subregions in the same region,
 * shaped as { region_id, region_name } to match the DB region format.
 *
 * @param {string} countryValue - country value (ISO code or DB UUID)
 * @param {string} countryLabel - country name
 * @param {string} countryCode  - 2-letter ISO code (lowercase OK)
 * @returns {{ region_id: string, region_name: string }[]}
 */
export function getStaticRegionsForCountry(countryValue, countryLabel, countryCode) {
  const code = (countryCode || '').toUpperCase()
  const name = (countryLabel || '').toLowerCase()

  // Find this country in our static list
  const match = WORLD_COUNTRIES.find(
    c => c.code === code || c.name.toLowerCase() === name
  )
  if (!match) return []

  // Return all subregions in the same world-region as distinct options
  const sibs = [...new Set(
    WORLD_COUNTRIES
      .filter(c => c.region === match.region)
      .map(c => c.subregion)
  )].sort()

  return sibs.map(sub => ({
    region_id:   `static-${sub.replace(/\s+/g, '-').toLowerCase()}`,
    region_name: sub,
    is_static:   true,   // lets the form know this is a fallback
  }))
}

/**
 * Convert world country data to the shape expected by SearchableSelect.
 * Merges with DB country list — DB records take priority (they have IDs for saving).
 *
 * @param {Array} dbCountries - Countries from backend API ({ country_id, country_name, flag_url })
 * @returns {Array} Merged list in SearchableSelect option format
 */
export function buildCountryOptions(dbCountries = []) {
  const dbByName = new Map(
    dbCountries.map(c => [c.country_name?.toLowerCase(), c])
  )
  const dbByCode = new Map(
    dbCountries.map(c => [
      (c.country_code || c.code || '').toLowerCase(),
      c,
    ])
  )

  const seen = new Set()
  const options = []

  // DB countries first — they have IDs
  for (const c of dbCountries) {
    const key = c.country_id
    if (seen.has(key)) continue
    seen.add(key)
    options.push({
      value: c.country_id,
      label: c.country_name,
      code: (c.country_code || c.code || '').toLowerCase(),
      flag_url: c.flag_url || getFlagUrl(c.country_code || c.code || ''),
      region: c.region || '',
      subregion: c.subregion || '',
      fromDB: true,
    })
  }

  // Fill in world countries not covered by DB
  for (const wc of WORLD_COUNTRIES) {
    const inDB =
      dbByCode.has(wc.code.toLowerCase()) ||
      dbByName.has(wc.name.toLowerCase())
    if (inDB) continue

    const key = `world-${wc.code}`
    if (seen.has(key)) continue
    seen.add(key)

    options.push({
      value: wc.code,     // use ISO code as fallback ID when no DB entry exists
      label: wc.name,
      code: wc.code.toLowerCase(),
      flag_url: getFlagUrl(wc.code),
      region: wc.region,
      subregion: wc.subregion,
      fromDB: false,
    })
  }

  return options.sort((a, b) => a.label.localeCompare(b.label))
}
