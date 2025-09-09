'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowLeftIcon as ArrowLeft, 
  ArrowRightIcon as ArrowRight, 
  CalendarIcon as Calendar,
  DocumentTextIcon as FileText,
  MapPinIcon as MapPin,
  BriefcaseIcon as Briefcase,
  AcademicCapIcon as GraduationCap,
  HeartIcon as Heart,
  BuildingOfficeIcon as Building,
  ArrowPathIcon as Loader2,
  CheckIcon as Check,
  ExclamationCircleIcon as AlertCircle,
  ClockIcon as Clock
} from '@heroicons/react/24/outline';
import { useRouter } from 'next/navigation';
import { format, addMonths } from 'date-fns';
import { toast } from 'react-hot-toast';
import ConfirmationModal from './ConfirmationModal';
import { useChat } from '@/components/chat/ChatProvider';

// Types
interface MigrationContext {
  originCountry: string;
  destinationCountry: string;
  purpose: string;
  timeline: string;
  initialQuery?: string;
  answers: Record<string, any>;
}

interface Question {
  id: string;
  type: 'select' | 'multiselect' | 'text' | 'date' | 'number' | 'radio';
  question: string;
  description?: string;
  options?: Array<{ value: string; label: string; icon?: any }>;
  validation?: {
    required?: boolean;
    min?: number;
    max?: number;
    pattern?: string;
  };
  conditional?: {
    dependsOn: string;
    values: string[];
  };
}

// Step definitions
const MIGRATION_STEPS = [
  { id: 'context', title: 'Migration Context', icon: MapPin },
  { id: 'purpose', title: 'Purpose & Timeline', icon: Briefcase },
  { id: 'analysis', title: 'AI Analysis', icon: Loader2 },
];

// Purpose options with icons
const PURPOSE_OPTIONS = [
  { value: 'work', label: 'Employment', icon: Briefcase, description: 'Work visa, job relocation' },
  { value: 'study', label: 'Education', icon: GraduationCap, description: 'Student visa, academic programs' },
  { value: 'family', label: 'Family Reunion', icon: Heart, description: 'Spouse, dependent visas' },
  { value: 'business', label: 'Business/Investment', icon: Building, description: 'Entrepreneur, investor visas' },
];

// Country lists
const COUNTRIES = [
  { code: 'IN', name: 'India', flag: '🇮🇳' },
  { code: 'US', name: 'United States', flag: '🇺🇸' },
  { code: 'UK', name: 'United Kingdom', flag: '🇬🇧' },
  { code: 'DE', name: 'Germany', flag: '🇩🇪' },
  { code: 'CA', name: 'Canada', flag: '🇨🇦' },
  { code: 'AU', name: 'Australia', flag: '🇦🇺' },
  { code: 'FR', name: 'France', flag: '🇫🇷' },
  { code: 'NL', name: 'Netherlands', flag: '🇳🇱' },
  { code: 'CH', name: 'Switzerland', flag: '🇨🇭' },
  { code: 'SG', name: 'Singapore', flag: '🇸🇬' },
  { code: 'JP', name: 'Japan', flag: '🇯🇵' },
  { code: 'AE', name: 'UAE', flag: '🇦🇪' },
];

export default function NewMigrationPlan() {
  const router = useRouter();
  const { updateContext: updateChatContext } = useChat();
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [context, setContext] = useState<MigrationContext>({
    originCountry: '',
    destinationCountry: '',
    purpose: '',
    timeline: '',
    answers: {},
  });
  const [dynamicQuestions, setDynamicQuestions] = useState<Question[]>([]);
  const [analysisResult, setAnalysisResult] = useState<any>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleAutoFill = async () => {
    const { originCountry, destinationCountry, purpose } = context;

    // Animate the selection of the origin country
    if (originCountry) {
      await new Promise(resolve => setTimeout(resolve, 500));
      setContext(prev => ({ ...prev, originCountry }));
    }

    // Animate the selection of the destination country
    if (destinationCountry) {
      await new Promise(resolve => setTimeout(resolve, 500));
      setContext(prev => ({ ...prev, destinationCountry }));
    }

    // Move to the next step
    setCurrentStep(1);

    // Animate the selection of the purpose
    if (purpose) {
      await new Promise(resolve => setTimeout(resolve, 500));
      setContext(prev => ({ ...prev, purpose }));
    }

    // After auto-filling, proceed to the next step
    await new Promise(resolve => setTimeout(resolve, 500));
    handleNext();
  };

  // Load initial context if exists
  useEffect(() => {
    const migrationContext = sessionStorage.getItem('migrationContext');
    if (migrationContext) {
      const parsedContext = JSON.parse(migrationContext);
      setContext(prev => ({ ...prev, ...parsedContext }));
      setIsModalOpen(true); // Open the modal
      sessionStorage.removeItem('migrationContext');
    } else {
      const initialQuery = sessionStorage.getItem('initialQuery');
    }
  }, []);

  const handleNext = async () => {
    if (currentStep === 1 && context.originCountry && context.destinationCountry && context.purpose) {
      // Update chat context with current migration plan
      updateChatContext({
        fromCountry: context.originCountry,
        toCountry: context.destinationCountry,
        purpose: context.purpose,
        timeline: context.timeline,
        currentStep: 'planning',
      });
      
      // Fetch dynamic questions from AI
      await fetchDynamicQuestions();
    } else if (currentStep === MIGRATION_STEPS.length - 2) {
      // Perform AI analsis
      await performAnalysis();
    }
    
    if (currentStep < MIGRATION_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const fetchDynamicQuestions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/vertex-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'generateQuestions',
          data: {
            origin: context.originCountry,
            destination: context.destinationCountry,
            purpose: context.purpose,
            timeline: context.timeline,
          },
        }),
      });

      const result = await response.json();
      if (result.success) {
        setDynamicQuestions(result.data.questions);
      }
    } catch (error) {
      console.error('Error fetching questions:', error);
      // Use fallback questions
      setDynamicQuestions(getFallbackQuestions());
    } finally {
      setIsLoading(false);
    }
  };

  const performAnalysis = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/vertex-agent', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: 'analyzeProfile',
          data: { answers: context },
        }),
      });

      const result = await response.json();
      if (result.success) {
        setAnalysisResult(result.data);
        toast.success('Analysis complete! Your migration plan is ready.');
      }
    } catch (error) {
      console.error('Error analyzing profile:', error);
      // Use mock analysis
      setAnalysisResult(getMockAnalysis());
    } finally {
      setIsLoading(false);
    }
  };

  const getFallbackQuestions = (): Question[] => {
    // Germany Student Visa specific questions
    if (context.destinationCountry === 'DE' && context.purpose === 'study') {
      return [
        {
          id: 'admission_status',
          type: 'radio',
          question: 'What is your admission status?',
          options: [
            { value: 'accepted', label: 'Accepted - Have admission letter' },
            { value: 'conditional', label: 'Conditional acceptance' },
            { value: 'applied', label: 'Applied, waiting for response' },
            { value: 'planning', label: 'Planning to apply' },
          ],
          validation: { required: true },
        },
        {
          id: 'german_proficiency',
          type: 'select',
          question: 'What is your German language proficiency?',
          description: 'Select your current level',
          options: [
            { value: 'none', label: 'No German knowledge' },
            { value: 'a1', label: 'A1 - Beginner' },
            { value: 'a2', label: 'A2 - Elementary' },
            { value: 'b1', label: 'B1 - Intermediate' },
            { value: 'b2', label: 'B2 - Upper Intermediate' },
            { value: 'c1', label: 'C1 - Advanced' },
            { value: 'c2', label: 'C2 - Proficient' },
          ],
        },
        {
          id: 'blocked_account',
          type: 'radio',
          question: 'Have you opened a blocked account?',
          description: 'Required amount: €11,208 for 2024',
          options: [
            { value: 'yes', label: 'Yes, already opened' },
            { value: 'in_progress', label: 'In progress' },
            { value: 'no', label: 'Not yet' },
          ],
        },
        {
          id: 'health_insurance',
          type: 'radio',
          question: 'Do you have German health insurance?',
          options: [
            { value: 'public', label: 'Yes, public insurance' },
            { value: 'private', label: 'Yes, private insurance' },
            { value: 'no', label: 'Not yet' },
          ],
        },
      ];
    }
    
    // Default questions for other routes
    return [
      {
        id: 'passport_status',
        type: 'radio',
        question: 'What is your passport status?',
        options: [
          { value: 'valid', label: 'Valid for 6+ months' },
          { value: 'expiring', label: 'Expiring soon' },
          { value: 'expired', label: 'Expired' },
          { value: 'none', label: 'No passport' },
        ],
        validation: { required: true },
      },
      {
        id: 'previous_visa',
        type: 'radio',
        question: 'Have you held a visa for the destination country?',
        options: [
          { value: 'yes', label: 'Yes' },
          { value: 'no', label: 'No' },
          { value: 'denied', label: 'Applied but denied' },
        ],
      },
    ];
  };

  const getMockAnalysis = () => ({
    recommendedVisa: 'German Student Visa',
    processingTime: '8-12 weeks',
    successProbability: 85,
    timeline: [
      { phase: 'Document Preparation', duration: '2 weeks', status: 'pending' },
      { phase: 'Blocked Account', duration: '1 week', status: 'pending' },
      { phase: 'Health Insurance', duration: '3 days', status: 'pending' },
      { phase: 'Visa Application', duration: '1 day', status: 'pending' },
      { phase: 'Appointment & Biometrics', duration: '2-4 weeks wait', status: 'pending' },
      { phase: 'Processing', duration: '6-8 weeks', status: 'pending' },
    ],
    requirements: {
      documents: [
        'Valid Passport',
        'University Admission Letter',
        'Blocked Account Proof (€11,208)',
        'Health Insurance',
        'Academic Transcripts',
        'Language Certificates',
        'CV/Resume',
        'Motivation Letter',
      ],
      financial: '€11,208 blocked account + €110 visa fee',
      language: 'English proficiency (IELTS/TOEFL) or German (if program in German)',
    },
    nextSteps: [
      'Open blocked account with approved provider',
      'Get health insurance coverage',
      'Book visa appointment at German Consulate',
      'Prepare all documents with translations',
    ],
  });

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return <ContextStep context={context} setContext={setContext} countries={COUNTRIES} />;
      case 1:
        return <PurposeStep context={context} setContext={setContext} purposes={PURPOSE_OPTIONS} />;
      case 2:
        return <DynamicQuestionsStep 
          questions={dynamicQuestions} 
          context={context} 
          setContext={setContext}
          stepIndex={0} // Only one dynamic step now
        />;
      case 3:
        return <AnalysisStep analysis={analysisResult} isLoading={isLoading} />;
      default:
        return null;
    }
  };

  const progress = ((currentStep + 1) / MIGRATION_STEPS.length) * 100;

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <div className="bg-white border-b border-neutral-200">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <button
              onClick={() => router.push('/dashboard')}
              className="flex items-center text-neutral-600 hover:text-neutral-900"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Dashboard
            </button>
            <div className="text-sm text-neutral-600">
              Step {currentStep + 1} of {MIGRATION_STEPS.length}
            </div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-4">
            <div className="flex items-center justify-between mb-2">
              {MIGRATION_STEPS.map((step, index) => (
                <div
                  key={step.id}
                  className={`flex items-center ${
                    index < MIGRATION_STEPS.length - 1 ? 'flex-1' : ''
                  }`}
                >
                  <div
                    className={`flex items-center justify-center w-10 h-10 rounded-full border-2 ${
                      index < currentStep
                        ? 'bg-primary-500 border-primary-500 text-white'
                        : index === currentStep
                        ? 'bg-white border-primary-500 text-primary-500'
                        : 'bg-white border-neutral-300 text-neutral-400'
                    }`}
                  >
                    {index < currentStep ? (
                      <Check className="w-5 h-5" />
                    ) : (
                      <step.icon className="w-5 h-5" />
                    )}
                  </div>
                  {index < MIGRATION_STEPS.length - 1 && (
                    <div
                      className={`flex-1 h-0.5 mx-2 ${
                        index < currentStep ? 'bg-primary-500' : 'bg-neutral-200'
                      }`}
                    />
                  )}
                </div>
              ))}
            </div>
            <div className="flex justify-between text-xs text-neutral-600">
              {MIGRATION_STEPS.map((step) => (
                <div key={step.id} className="text-center" style={{ width: `${100 / MIGRATION_STEPS.length}%` }}>
                  {step.title}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ConfirmationModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onConfirm={() => {
            setIsModalOpen(false);
            handleAutoFill();
          }}
          context={context}
        />
        <AnimatePresence mode="wait">
          <motion.div
            key={currentStep}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {renderStepContent()}
          </motion.div>
        </AnimatePresence>

        {/* Navigation Buttons */}
        <div className="flex justify-between mt-8">
          <button
            onClick={handleBack}
            disabled={currentStep === 0}
            className="btn-outline px-6 py-3 flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Previous
          </button>
          
          {currentStep < MIGRATION_STEPS.length - 1 ? (
            <button
              onClick={handleNext}
              disabled={isLoading}
              className="btn-primary px-6 py-3 flex items-center"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  Next
                  <ArrowRight className="w-4 h-4 ml-2" />
                </>
              )}
            </button>
          ) : (
            <button
              onClick={() => router.push('/dashboard')}
              className="btn-primary px-6 py-3"
            >
              View Dashboard
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// Step Components

function ContextStep({ context, setContext, countries }: any) {
  return (
    <div className="card p-8">
      <h2 className="text-2xl font-bold text-neutral-900 mb-2">
        Where are you migrating from and to?
      </h2>
      <p className="text-neutral-600 mb-8">
        Select your current location and desired destination
      </p>

      <div className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-3">
            Current Country
          </label>
          <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
            {countries.map((country: any) => (
              <button
                key={country.code}
                onClick={() => setContext({ ...context, originCountry: country.code })}
                className={`p-4 rounded-lg border-2 transition-all ${
                  context.originCountry === country.code
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-neutral-200 hover:border-primary-300'
                }`}
              >
                <div className="text-2xl mb-1">{country.flag}</div>
                <div className="text-sm font-medium text-neutral-900">{country.name}</div>
              </button>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-neutral-700 mb-3">
            Destination Country
          </label>
          <div className="grid grid-cols-3 sm:grid-cols-4 gap-3">
            {countries.filter((c: any) => c.code !== context.originCountry).map((country: any) => (
              <button
                key={country.code}
                onClick={() => setContext({ ...context, destinationCountry: country.code })}
                className={`p-4 rounded-lg border-2 transition-all ${
                  context.destinationCountry === country.code
                    ? 'border-primary-500 bg-primary-50'
                    : 'border-neutral-200 hover:border-primary-300'
                }`}
              >
                <div className="text-2xl mb-1">{country.flag}</div>
                <div className="text-sm font-medium text-neutral-900">{country.name}</div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function PurposeStep({ context, setContext, purposes }: any) {
  return (
    <div className="card p-8">
      <h2 className="text-2xl font-bold text-neutral-900 mb-2">
        What's your purpose of migration?
      </h2>
      <p className="text-neutral-600 mb-8">
        This helps us determine the right visa category and requirements
      </p>

      <div className="grid sm:grid-cols-2 gap-4 mb-8">
        {purposes.map((purpose: any) => (
          <button
            key={purpose.value}
            onClick={() => setContext({ ...context, purpose: purpose.value })}
            className={`p-6 rounded-lg border-2 text-left transition-all ${
              context.purpose === purpose.value
                ? 'border-primary-500 bg-primary-50'
                : 'border-neutral-200 hover:border-primary-300'
            }`}
          >
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-white rounded-lg">
                <purpose.icon className="w-6 h-6 text-primary-600" />
              </div>
              <div>
                <h3 className="font-semibold text-neutral-900">{purpose.label}</h3>
                <p className="text-sm text-neutral-600 mt-1">{purpose.description}</p>
              </div>
            </div>
          </button>
        ))}
      </div>

      <div>
        <label className="block text-sm font-medium text-neutral-700 mb-3">
          When do you plan to migrate?
        </label>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {['ASAP', '1-3 months', '3-6 months', '6-12 months'].map((timeline) => (
            <button
              key={timeline}
              onClick={() => setContext({ ...context, timeline })}
              className={`py-3 px-4 rounded-lg border-2 transition-all ${
                context.timeline === timeline
                  ? 'border-primary-500 bg-primary-50 text-primary-700'
                  : 'border-neutral-200 hover:border-primary-300'
              }`}
            >
              <Clock className="w-4 h-4 mx-auto mb-1" />
              <div className="text-sm font-medium">{timeline}</div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function DynamicQuestionsStep({ questions, context, setContext, stepIndex }: any) {
  const stepQuestions = questions.slice(stepIndex * 2, (stepIndex + 1) * 2);
  
  if (stepQuestions.length === 0) {
    return (
      <div className="card p-8 text-center">
        <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-primary-500" />
        <p className="text-neutral-600">Loading questions...</p>
      </div>
    );
  }

  return (
    <div className="card p-8">
      <h2 className="text-2xl font-bold text-neutral-900 mb-8">
        Additional Information
      </h2>
      
      <div className="space-y-6">
        {stepQuestions.map((question: Question) => (
          <div key={question.id}>
            <label className="block text-sm font-medium text-neutral-700 mb-2">
              {question.question}
            </label>
            {question.description && (
              <p className="text-sm text-neutral-600 mb-3">{question.description}</p>
            )}
            
            {question.type === 'radio' && (
              <div className="space-y-2">
                {question.options?.map((option) => (
                  <label
                    key={option.value}
                    className="flex items-center p-3 rounded-lg border border-neutral-200 hover:border-primary-300 cursor-pointer"
                  >
                    <input
                      type="radio"
                      name={question.id}
                      value={option.value}
                      checked={context.answers[question.id] === option.value}
                      onChange={(e) => setContext({
                        ...context,
                        answers: { ...context.answers, [question.id]: e.target.value }
                      })}
                      className="mr-3"
                    />
                    <span className="text-neutral-900">{option.label}</span>
                  </label>
                ))}
              </div>
            )}
            
            {question.type === 'select' && (
              <select
                value={context.answers[question.id] || ''}
                onChange={(e) => setContext({
                  ...context,
                  answers: { ...context.answers, [question.id]: e.target.value }
                })}
                className="input"
              >
                <option value="">Select an option</option>
                {question.options?.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function AnalysisStep({ analysis, isLoading }: any) {
  if (isLoading || !analysis) {
    return (
      <div className="card p-12 text-center">
        <Loader2 className="w-12 h-12 animate-spin mx-auto mb-4 text-primary-500" />
        <h3 className="text-xl font-semibold text-neutral-900 mb-2">
          Analyzing Your Profile
        </h3>
        <p className="text-neutral-600">
          Our AI is creating your personalized migration plan...
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Success Message */}
      <div className="card p-6 border-primary-200 bg-primary-50">
        <div className="flex items-start space-x-4">
          <div className="p-2 bg-primary-100 rounded-lg">
            <Check className="w-6 h-6 text-primary-600" />
          </div>
          <div>
            <h3 className="font-semibold text-neutral-900 mb-1">
              Your Migration Plan is Ready!
            </h3>
            <p className="text-neutral-600">
              Based on your profile, we recommend the <strong>{analysis.recommendedVisa}</strong> with
              an estimated processing time of <strong>{analysis.processingTime}</strong>.
            </p>
          </div>
        </div>
      </div>

      {/* Timeline */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">
          Your Migration Timeline
        </h3>
        <div className="space-y-3">
          {analysis.timeline.map((phase: any, index: number) => (
            <div key={index} className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-primary-100 rounded-full flex items-center justify-center">
                  <span className="text-sm font-medium text-primary-700">{index + 1}</span>
                </div>
              </div>
              <div className="flex-grow">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-neutral-900">{phase.phase}</span>
                  <span className="text-sm text-neutral-600">{phase.duration}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Requirements */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">
          Document Requirements
        </h3>
        <div className="grid sm:grid-cols-2 gap-3">
          {analysis.requirements.documents.map((doc: string, index: number) => (
            <div key={index} className="flex items-center space-x-2">
              <FileText className="w-4 h-4 text-neutral-400" />
              <span className="text-neutral-700">{doc}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Next Steps */}
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-neutral-900 mb-4">
          Immediate Next Steps
        </h3>
        <ol className="space-y-2">
          {analysis.nextSteps.map((step: string, index: number) => (
            <li key={index} className="flex items-start space-x-3">
              <span className="flex-shrink-0 w-6 h-6 bg-primary-100 text-primary-700 rounded-full flex items-center justify-center text-sm font-medium">
                {index + 1}
              </span>
              <span className="text-neutral-700">{step}</span>
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

