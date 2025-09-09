'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ArrowLeftIcon as ArrowLeft, 
  ArrowRightIcon as ArrowRight, 
  CheckIcon as Check,
  XMarkIcon as XMark,
  MapPinIcon as MapPin,
  ClockIcon as Clock,
  BriefcaseIcon as Briefcase,
  AcademicCapIcon as GraduationCap,
  HeartIcon as Heart,
  BuildingOfficeIcon as Building
} from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';
import { getLocationDisplay } from '@/lib/utils/countries';

const PURPOSE_ICONS = {
  work: Briefcase,
  study: GraduationCap,
  family: Heart,
  business: Building,
};

export default function VerificationPage() {
  const router = useRouter();
  const [migrationData, setMigrationData] = useState<any>(null);
  const [isVerified, setIsVerified] = useState(false);

  useEffect(() => {
    const storedData = sessionStorage.getItem('migrationContext');
    if (storedData) {
      setMigrationData(JSON.parse(storedData));
    } else {
      router.push('/');
    }
  }, [router]);

  const handleVerify = () => {
    setIsVerified(true);
    // Store verified data and proceed to next step
    sessionStorage.setItem('verifiedMigrationContext', JSON.stringify(migrationData));
    setTimeout(() => {
      router.push('/migration/documents');
    }, 1000);
  };

  const handleEdit = () => {
    router.push('/');
  };

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

  const PurposeIcon = PURPOSE_ICONS[migrationData.purpose as keyof typeof PURPOSE_ICONS] || Briefcase;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <button
              onClick={() => router.push('/')}
              className="flex items-center text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Home
            </button>
            <div className="text-sm text-gray-600">
              Verify Your Information
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
            Please Verify Your Information
          </h1>
          <p className="text-lg text-gray-600">
            Review the details below and confirm they are correct before proceeding
          </p>
        </motion.div>

        {/* Verification Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 mb-8"
        >
          <div className="space-y-6">
            {/* Migration Route */}
            <div className="flex items-center justify-center space-x-4 p-6 bg-blue-50 rounded-xl">
              <div className="flex items-center space-x-2">
                <MapPin className="w-5 h-5 text-blue-600" />
                <span className="text-lg font-semibold text-gray-900">
                  {getLocationDisplay(migrationData.originCountry, migrationData.originCity)} → {getLocationDisplay(migrationData.destinationCountry, migrationData.destinationCity)}
                </span>
              </div>
            </div>

            {/* Purpose */}
            <div className="flex items-center justify-center space-x-4 p-6 bg-green-50 rounded-xl">
              <PurposeIcon className="w-6 h-6 text-green-600" />
              <div className="text-center">
                <p className="text-sm text-gray-600">Purpose of Migration</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {migrationData.purpose}
                </p>
              </div>
            </div>

            {/* Timeline */}
            <div className="flex items-center justify-center space-x-4 p-6 bg-purple-50 rounded-xl">
              <Clock className="w-6 h-6 text-purple-600" />
              <div className="text-center">
                <p className="text-sm text-gray-600">Timeline</p>
                <p className="text-lg font-semibold text-gray-900">
                  {migrationData.timeline}
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Action Buttons */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="flex justify-center space-x-4"
        >
          <button
            onClick={handleEdit}
            className="flex items-center px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <XMark className="w-5 h-5 mr-2" />
            Edit Information
          </button>
          
          <button
            onClick={handleVerify}
            disabled={isVerified}
            className="flex items-center px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
          >
            {isVerified ? (
              <>
                <Check className="w-5 h-5 mr-2" />
                Verified!
              </>
            ) : (
              <>
                <Check className="w-5 h-5 mr-2" />
                Confirm & Continue
              </>
            )}
          </button>
        </motion.div>

        {/* Success Message */}
        {isVerified && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3 }}
            className="mt-6 text-center"
          >
            <div className="inline-flex items-center px-4 py-2 bg-green-100 text-green-800 rounded-lg">
              <Check className="w-5 h-5 mr-2" />
              Information verified! Redirecting to next step...
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}
