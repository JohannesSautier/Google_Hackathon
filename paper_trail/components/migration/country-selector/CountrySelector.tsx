import { FC } from 'react';
import { GlobeAltIcon as Globe } from '@heroicons/react/24/outline';
import Image from 'next/image';

interface CountrySelectorProps {
  onSelect: (country: string) => void;
  selectedCountry?: string;
  type: 'origin' | 'destination';
}

const CountrySelector: FC<CountrySelectorProps> = ({ onSelect, selectedCountry, type }) => {
  return (
    <div className="p-6 bg-white rounded-xl shadow-sm border border-gray-100">
      <div className="flex items-center mb-4">
        <Globe className="w-5 h-5 text-blue-500 mr-2" />
        <h3 className="text-lg font-semibold text-gray-900">
          {type === 'origin' ? 'Where are you from?' : 'Where are you going?'}
        </h3>
      </div>
      
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">
        {/* This would be populated with actual country data */}
        {['Germany', 'India', 'Brazil', 'Portugal', 'Netherlands', 'Sweden'].map((country) => (
          <button
            key={country}
            onClick={() => onSelect(country)}
            className={`p-4 rounded-lg border transition-all ${
              selectedCountry === country
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-blue-300'
            }`}
          >
            <div className="text-center">
              {/* Replace with actual country flags */}
              <div className="w-10 h-10 mx-auto mb-2 rounded-full bg-gray-100" />
              <span className="text-sm font-medium text-gray-700">{country}</span>
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default CountrySelector;
