'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ArrowLeftIcon as ArrowLeft, 
  ArrowRightIcon as ArrowRight, 
  DocumentTextIcon as Document,
  CheckCircleIcon as CheckCircle,
  ExclamationTriangleIcon as AlertTriangle,
  ClockIcon as Clock,
  BriefcaseIcon as Briefcase,
  AcademicCapIcon as GraduationCap,
  HeartIcon as Heart,
  BuildingOfficeIcon as Building
} from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';
import { getCountryName } from '@/lib/utils/countries';

const PURPOSE_ICONS = {
  work: Briefcase,
  study: GraduationCap,
  family: Heart,
  business: Building,
};

const PURPOSE_SPECIFIC_QUESTIONS = {
  work: {
    title: 'Do you have a job contract or offer letter?',
    description: 'A valid employment contract or job offer from a company in your destination country',
    options: [
      { value: 'yes', label: 'Yes, I have a contract/offer letter' },
      { value: 'pending', label: 'Pending - waiting for response' },
      { value: 'no', label: 'No, I need to find a job first' },
    ]
  },
  study: {
    title: 'Do you have a university admission letter?',
    description: 'An acceptance letter from a recognized educational institution',
    options: [
      { value: 'yes', label: 'Yes, I have an admission letter' },
      { value: 'conditional', label: 'Conditional admission' },
      { value: 'applied', label: 'Applied, waiting for response' },
      { value: 'no', label: 'No, I need to apply first' },
    ]
  },
  family: {
    title: 'Do you have a family invitation letter?',
    description: 'An invitation letter from family members in your destination country',
    options: [
      { value: 'yes', label: 'Yes, I have an invitation letter' },
      { value: 'pending', label: 'Pending - family is preparing it' },
      { value: 'no', label: 'No, I need to get one first' },
    ]
  },
  business: {
    title: 'Do you have business documents or investment proof?',
    description: 'Business registration, investment certificates, or business plan',
    options: [
      { value: 'yes', label: 'Yes, I have all required documents' },
      { value: 'partial', label: 'Partially - some documents missing' },
      { value: 'no', label: 'No, I need to prepare them' },
    ]
  },
};

export default function DocumentsPage() {
  const router = useRouter();
  const [migrationData, setMigrationData] = useState<any>(null);
  const [formData, setFormData] = useState({
    passportStatus: '',
    passportValidity: '',
    visaStatus: '',
    purposeSpecific: '',
  });

  useEffect(() => {
    const storedData = sessionStorage.getItem('verifiedMigrationContext');
    if (storedData) {
      setMigrationData(JSON.parse(storedData));
    } else {
      router.push('/');
    }
  }, [router]);

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleNext = () => {
    // Validate required fields
    const requiredFields = ['passportStatus', 'visaStatus', 'purposeSpecific'];
    const isFormValid = requiredFields.every(field => formData[field as keyof typeof formData]);
    
    if (isFormValid) {
      // Store the document data
      const documentData = {
        ...migrationData,
        ...formData,
      };
      
      sessionStorage.setItem('documentContext', JSON.stringify(documentData));
      router.push('/migration/analysis');
    }
  };

  const isFormValid = formData.passportStatus && formData.visaStatus && formData.purposeSpecific;

  if (!migrationData) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  const purposeQuestion = PURPOSE_SPECIFIC_QUESTIONS[migrationData.purpose as keyof typeof PURPOSE_SPECIFIC_QUESTIONS];
  const PurposeIcon = PURPOSE_ICONS[migrationData.purpose as keyof typeof PURPOSE_ICONS] || Briefcase;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <button
              onClick={() => router.push('/migration/verify')}
              className="flex items-center text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Verification
            </button>
            <div className="text-sm text-gray-600">
              Document Status
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-8"
        >
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Document Status Check
          </h1>
          <p className="text-lg text-gray-600">
            Let us know about your current document status
          </p>
        </motion.div>

        <div className="space-y-8">
          {/* Passport Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="bg-white rounded-xl shadow-lg border border-gray-200 p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <Document className="w-6 h-6 text-blue-600" />
              <h2 className="text-xl font-semibold text-gray-900">Passport Status</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Do you have a valid passport?
                </label>
                <div className="space-y-2">
                  {[
                    { value: 'valid', label: 'Yes, valid for 6+ months', icon: CheckCircle, color: 'text-green-600' },
                    { value: 'expiring', label: 'Valid but expiring soon (less than 6 months)', icon: AlertTriangle, color: 'text-yellow-600' },
                    { value: 'expired', label: 'Expired', icon: AlertTriangle, color: 'text-red-600' },
                    { value: 'none', label: 'No passport', icon: AlertTriangle, color: 'text-red-600' },
                  ].map((option) => (
                    <label
                      key={option.value}
                      className="flex items-center p-3 rounded-lg border border-gray-200 hover:border-blue-300 cursor-pointer"
                    >
                      <input
                        type="radio"
                        name="passportStatus"
                        value={option.value}
                        checked={formData.passportStatus === option.value}
                        onChange={(e) => handleInputChange('passportStatus', e.target.value)}
                        className="mr-3"
                      />
                      <option.icon className={`w-5 h-5 mr-3 ${option.color}`} />
                      <span className="text-gray-900">{option.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              {formData.passportStatus === 'expiring' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    How long is your passport valid?
                  </label>
                  <select
                    value={formData.passportValidity}
                    onChange={(e) => handleInputChange('passportValidity', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="">Select validity period</option>
                    <option value="1-3 months">1-3 months</option>
                    <option value="3-6 months">3-6 months</option>
                    <option value="6+ months">6+ months</option>
                  </select>
                </div>
              )}
            </div>
          </motion.div>

          {/* Visa Status */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-white rounded-xl shadow-lg border border-gray-200 p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <Document className="w-6 h-6 text-green-600" />
              <h2 className="text-xl font-semibold text-gray-900">Visa Status</h2>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Do you have a valid visa for {getCountryName(migrationData.destinationCountry)}?
              </label>
              <div className="space-y-2">
                {[
                  { value: 'yes', label: 'Yes, I have a valid visa', icon: CheckCircle, color: 'text-green-600' },
                  { value: 'applied', label: 'Applied, waiting for response', icon: Clock, color: 'text-yellow-600' },
                  { value: 'denied', label: 'Applied but was denied', icon: AlertTriangle, color: 'text-red-600' },
                  { value: 'no', label: 'No, I need to apply', icon: AlertTriangle, color: 'text-red-600' },
                ].map((option) => (
                  <label
                    key={option.value}
                    className="flex items-center p-3 rounded-lg border border-gray-200 hover:border-blue-300 cursor-pointer"
                  >
                    <input
                      type="radio"
                      name="visaStatus"
                      value={option.value}
                      checked={formData.visaStatus === option.value}
                      onChange={(e) => handleInputChange('visaStatus', e.target.value)}
                      className="mr-3"
                    />
                    <option.icon className={`w-5 h-5 mr-3 ${option.color}`} />
                    <span className="text-gray-900">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Purpose-Specific Question */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="bg-white rounded-xl shadow-lg border border-gray-200 p-6"
          >
            <div className="flex items-center space-x-3 mb-4">
              <PurposeIcon className="w-6 h-6 text-purple-600" />
              <h2 className="text-xl font-semibold text-gray-900">{purposeQuestion.title}</h2>
            </div>
            
            <p className="text-gray-600 mb-4">{purposeQuestion.description}</p>
            
            <div className="space-y-2">
              {purposeQuestion.options.map((option) => (
                <label
                  key={option.value}
                  className="flex items-center p-3 rounded-lg border border-gray-200 hover:border-blue-300 cursor-pointer"
                >
                  <input
                    type="radio"
                    name="purposeSpecific"
                    value={option.value}
                    checked={formData.purposeSpecific === option.value}
                    onChange={(e) => handleInputChange('purposeSpecific', e.target.value)}
                    className="mr-3"
                  />
                  <span className="text-gray-900">{option.label}</span>
                </label>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="flex justify-center mt-8"
        >
          <button
            onClick={handleNext}
            disabled={!isFormValid}
            className="flex items-center px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
          >
            <span>Continue to Analysis</span>
            <ArrowRight className="w-5 h-5 ml-2" />
          </button>
        </motion.div>
      </div>
    </div>
  );
}
