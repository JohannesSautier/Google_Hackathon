// Country code to name mapping
export const COUNTRY_NAMES: { [key: string]: string } = {
  'IN': 'India',
  'US': 'United States',
  'UK': 'United Kingdom',
  'DE': 'Germany',
  'CA': 'Canada',
  'AU': 'Australia',
  'FR': 'France',
  'NL': 'Netherlands',
  'CH': 'Switzerland',
  'SG': 'Singapore',
  'JP': 'Japan',
  'AE': 'UAE',
};

// Helper function to get country name from code
export const getCountryName = (code: string): string => {
  return COUNTRY_NAMES[code] || code;
};

// Helper function to get location display (city, country)
export const getLocationDisplay = (countryCode: string, city?: string): string => {
  const countryName = getCountryName(countryCode);
  return city ? `${city}, ${countryName}` : countryName;
};
