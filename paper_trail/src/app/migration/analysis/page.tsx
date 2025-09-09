'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  ArrowLeftIcon as ArrowLeft, 
  ArrowRightIcon as ArrowRight, 
  CheckCircleIcon as CheckCircle,
  ClockIcon as Clock,
  ExclamationTriangleIcon as AlertTriangle,
  DocumentTextIcon as Document,
  ShieldCheckIcon as Shield,
  BanknotesIcon as Banknotes,
  CurrencyDollarIcon as CurrencyDollar,
  PaperAirplaneIcon as PaperAirplane,
  ArrowPathIcon as Loader2
} from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';

const MIGRATION_STAGES = [
  {
    id: 'visa',
    title: 'Visa Application',
    description: 'Submit your visa application and required documents',
    icon: Document,
    color: 'blue',
    estimatedTime: '2-4 weeks',
    dependencies: [],
  },
  {
    id: 'insurance',
    title: 'Health Insurance',
    description: 'Obtain mandatory health insurance coverage',
    icon: Shield,
    color: 'green',
    estimatedTime: '1-2 weeks',
    dependencies: ['visa'],
  },
  {
    id: 'bank',
    title: 'Bank Account',
    description: 'Open a bank account in your destination country',
    icon: Banknotes,
    color: 'purple',
    estimatedTime: '1-3 weeks',
    dependencies: ['visa', 'insurance'],
  },
  {
    id: 'income',
    title: 'Proof of Income',
    description: 'Provide financial documentation and proof of funds',
    icon: CurrencyDollar,
    color: 'orange',
    estimatedTime: '1-2 weeks',
    dependencies: ['bank'],
  },
  {
    id: 'flight',
    title: 'Flight Options',
    description: 'Book your flight and finalize travel arrangements',
    icon: PaperAirplane,
    color: 'indigo',
    estimatedTime: '1 week',
    dependencies: ['visa', 'insurance', 'bank', 'income'],
  },
];

export default function AnalysisPage() {
  const router = useRouter();
  const [migrationData, setMigrationData] = useState<any>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const [analysisComplete, setAnalysisComplete] = useState(false);

  useEffect(() => {
    const storedData = sessionStorage.getItem('documentContext');
    if (storedData) {
      setMigrationData(JSON.parse(storedData));
    } else {
      router.push('/');
    }

    // Simulate analysis process
    setTimeout(() => {
      setIsAnalyzing(false);
      setAnalysisComplete(true);
    }, 3000);
  }, [router]);

  const getStageStatus = (stage: any) => {
    if (!analysisComplete) return 'pending';
    
    // Simple logic based on document status
    if (stage.id === 'visa') {
      if (migrationData?.visaStatus === 'yes') return 'completed';
      if (migrationData?.visaStatus === 'applied') return 'in-progress';
      return 'pending';
    }
    
    if (stage.id === 'insurance') {
      return 'pending'; // Always pending as it depends on visa
    }
    
    if (stage.id === 'bank') {
      return 'pending'; // Always pending as it depends on visa and insurance
    }
    
    if (stage.id === 'income') {
      return 'pending'; // Always pending as it depends on bank
    }
    
    if (stage.id === 'flight') {
      return 'pending'; // Always pending as it depends on all previous stages
    }
    
    return 'pending';
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-500 text-white';
      case 'in-progress':
        return 'bg-blue-500 text-white';
      case 'pending':
        return 'bg-gray-300 text-gray-600';
      default:
        return 'bg-gray-300 text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return CheckCircle;
      case 'in-progress':
        return Clock;
      case 'pending':
        return Clock;
      default:
        return Clock;
    }
  };

  const handleContinue = () => {
    // Store analysis data and proceed to dashboard
    sessionStorage.setItem('analysisComplete', 'true');
    router.push('/dashboard');
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <button
              onClick={() => router.push('/migration/documents')}
              className="flex items-center text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Documents
            </button>
            <div className="text-sm text-gray-600">
              Migration Analysis
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="text-center mb-8"
        >
          <h1 className="text-3xl font-bold text-gray-900 mb-4">
            Your Migration Journey Analysis
          </h1>
          <p className="text-lg text-gray-600">
            Based on your information, here's your personalized migration roadmap
          </p>
        </motion.div>

        {/* Analysis Status */}
        {isAnalyzing && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6 }}
            className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 mb-8 text-center"
          >
            <Loader2 className="w-12 h-12 animate-spin text-blue-500 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Analyzing Your Migration Path
            </h3>
            <p className="text-gray-600">
              Our AI is creating your personalized migration timeline...
            </p>
          </motion.div>
        )}

        {/* Migration Stages */}
        {analysisComplete && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-white rounded-2xl shadow-xl border border-gray-200 p-8 mb-8"
          >
            <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
              Your Migration Stages
            </h2>
            
            {/* Horizontal Timeline */}
            <div className="relative">
              {/* Connection Lines */}
              <div className="absolute top-8 left-0 right-0 h-0.5 bg-gray-200"></div>
              
              <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
                {MIGRATION_STAGES.map((stage, index) => {
                  const status = getStageStatus(stage);
                  const StatusIcon = getStatusIcon(status);
                  const isLast = index === MIGRATION_STAGES.length - 1;
                  
                  return (
                    <motion.div
                      key={stage.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.6, delay: 0.3 + index * 0.1 }}
                      className="relative"
                    >
                      {/* Stage Card */}
                      <div className="text-center">
                        {/* Stage Icon */}
                        <div className={`relative w-16 h-16 mx-auto mb-4 rounded-full flex items-center justify-center ${getStatusColor(status)}`}>
                          <stage.icon className="w-8 h-8" />
                          {!isLast && (
                            <div className="absolute -right-2 top-1/2 transform -translate-y-1/2 w-4 h-0.5 bg-gray-200"></div>
                          )}
                        </div>
                        
                        {/* Stage Info */}
                        <h3 className="font-semibold text-gray-900 mb-2">{stage.title}</h3>
                        <p className="text-sm text-gray-600 mb-2">{stage.description}</p>
                        <div className="flex items-center justify-center space-x-1 text-xs text-gray-500">
                          <Clock className="w-3 h-3" />
                          <span>{stage.estimatedTime}</span>
                        </div>
                        
                        {/* Status Badge */}
                        <div className={`mt-2 inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          status === 'completed' ? 'bg-green-100 text-green-800' :
                          status === 'in-progress' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          <StatusIcon className="w-3 h-3 mr-1" />
                          {status === 'completed' ? 'Completed' :
                           status === 'in-progress' ? 'In Progress' :
                           'Pending'}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </motion.div>
        )}

        {/* Dependencies Info */}
        {analysisComplete && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="bg-blue-50 rounded-xl p-6 mb-8"
          >
            <div className="flex items-start space-x-3">
              <AlertTriangle className="w-6 h-6 text-blue-600 mt-1" />
              <div>
                <h3 className="font-semibold text-gray-900 mb-2">Important Note</h3>
                <p className="text-gray-700">
                  Each stage depends on the completion of previous stages. You must complete them in order:
                  <strong> Visa Application → Health Insurance → Bank Account → Proof of Income → Flight Booking</strong>
                </p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Action Buttons */}
        {analysisComplete && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="flex justify-center"
          >
            <button
              onClick={handleContinue}
              className="flex items-center px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
            >
              <span>Continue to Dashboard</span>
              <ArrowRight className="w-5 h-5 ml-2" />
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
}
