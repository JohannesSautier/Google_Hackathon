'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  CalendarIcon as Calendar,
  ClockIcon as Clock,
  ExclamationTriangleIcon as AlertTriangle,
  CheckCircleIcon as CheckCircle2,
  ArrowTrendingUpIcon as TrendingUp,
  DocumentTextIcon as FileText,
  UsersIcon as Users,
  StarIcon as Target,
  TrophyIcon as Award,
  ChevronRightIcon as ChevronRight,
  PlusIcon as Plus,
} from '@heroicons/react/24/outline';
import { CircularProgressbar, buildStyles } from 'react-circular-progressbar';
import 'react-circular-progressbar/dist/styles.css';
import { format, differenceInDays, addDays, isAfter, isBefore } from 'date-fns';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { mockTimeline, TimelineEvent } from '@/src/data/mockTimeline';
import { useChat } from '@/components/chat/ChatProvider';

// Types
interface MigrationPlan {
  id: string;
  title: string;
  fromCountry: string;
  toCountry: string;
  startDate: Date;
  targetDate: Date;
  currentPhase: number;
  totalPhases: number;
  progress: number;
  status: 'on-track' | 'at-risk' | 'delayed' | 'completed';
  nextDeadline: {
    title: string;
    date: Date;
    type: 'critical' | 'important' | 'normal';
  };
}


interface Achievement {
  id: string;
  title: string;
  description: string;
  icon: string;
  unlocked: boolean;
  progress: number;
  maxProgress: number;
}

// Mock data for demonstration
const mockPlans: MigrationPlan[] = [
  {
    id: '1',
    title: 'Germany Student Visa',
    fromCountry: 'India',
    toCountry: 'Germany',
    startDate: new Date('2025-01-01'),
    targetDate: new Date('2025-06-01'),
    currentPhase: 3,
    totalPhases: 8,
    progress: 37.5,
    status: 'on-track',
    nextDeadline: {
      title: 'Submit Blocked Account Proof',
      date: addDays(new Date(), 5),
      type: 'critical',
    },
  },
  {
    id: '2',
    title: 'Canada Work Permit',
    fromCountry: 'India',
    toCountry: 'Canada',
    startDate: new Date('2025-02-01'),
    targetDate: new Date('2025-08-01'),
    currentPhase: 1,
    totalPhases: 6,
    progress: 16.7,
    status: 'at-risk',
    nextDeadline: {
      title: 'Language Test Registration',
      date: addDays(new Date(), 2),
      type: 'important',
    },
  },
];


const mockAchievements: Achievement[] = [
  {
    id: '1',
    title: 'Early Bird',
    description: 'Start planning 6 months in advance',
    icon: '🏃',
    unlocked: true,
    progress: 1,
    maxProgress: 1,
  },
  {
    id: '2',
    title: 'Document Master',
    description: 'Upload 10 documents',
    icon: '📄',
    unlocked: false,
    progress: 7,
    maxProgress: 10,
  },
  {
    id: '3',
    title: 'Deadline Champion',
    description: 'Meet 5 deadlines on time',
    icon: '⏰',
    unlocked: false,
    progress: 3,
    maxProgress: 5,
  },
  {
    id: '4',
    title: 'Multi-Country Explorer',
    description: 'Create plans for 3 countries',
    icon: '🌍',
    unlocked: false,
    progress: 2,
    maxProgress: 3,
  },
];

// Mock migration news data
interface NewsItem {
  id: string;
  headline: string;
  date: Date;
  source: string;
  relevanceScore: number;
}

const mockMigrationNews: NewsItem[] = [
  {
    id: '1',
    headline: 'Germany Extends Student Visa Processing Times Due to High Demand from Indian Students',
    date: new Date('2025-01-05'),
    source: 'German Immigration News',
    relevanceScore: 95,
  },
  {
    id: '2',
    headline: 'New Financial Requirements for Indian Students Applying to German Universities in 2025',
    date: new Date('2025-01-03'),
    source: 'Education Today',
    relevanceScore: 90,
  },
  {
    id: '3',
    headline: 'German Blocked Account Amount Increased to €11,208 for 2025 Academic Year',
    date: new Date('2025-01-02'),
    source: 'Study in Germany Portal',
    relevanceScore: 88,
  },
  {
    id: '4',
    headline: 'Top German Cities Welcoming More International Students from India',
    date: new Date('2024-12-28'),
    source: 'Migration Weekly',
    relevanceScore: 85,
  },
  {
    id: '5',
    headline: 'German Language Test Requirements Updated for Student Visa Applications',
    date: new Date('2024-12-25'),
    source: 'Visa Updates Germany',
    relevanceScore: 83,
  },
  {
    id: '6',
    headline: 'Post-Study Work Rights Extended for STEM Graduates in Germany',
    date: new Date('2024-12-20'),
    source: 'Career Germany',
    relevanceScore: 80,
  },
  {
    id: '7',
    headline: 'Health Insurance Changes for International Students in Germany Starting 2025',
    date: new Date('2024-12-18'),
    source: 'Student Guide Germany',
    relevanceScore: 78,
  },
  {
    id: '8',
    headline: 'Indian Students Report 15% Faster Visa Processing Through New Digital Portal',
    date: new Date('2024-12-15'),
    source: 'Tech Migration News',
    relevanceScore: 75,
  },
];

export default function DashboardPage() {
  const router = useRouter();
  const { context, updateContext } = useChat();
  const [selectedPlan, setSelectedPlan] = useState<MigrationPlan>(mockPlans[0]);
  const [notifications, setNotifications] = useState(3);
  const [showAllEvents, setShowAllEvents] = useState(false);
  const [activeTab, setActiveTab] = useState<'timeline' | 'news'>('timeline');

  // Calculate statistics
  const upcomingDeadlines = mockTimeline.filter(
    (event) => event.status === 'upcoming' && event.priority === 'critical'
  ).length;

  const completedTasks = mockTimeline.filter(
    (event) => event.status === 'completed'
  ).length;

  const totalTasks = mockTimeline.length;
  const overallProgress = (completedTasks / totalTasks) * 100;

  // Get status color
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'on-track':
        return 'text-success-600 bg-success-50';
      case 'at-risk':
        return 'text-warning-600 bg-warning-50';
      case 'delayed':
        return 'text-danger-600 bg-danger-50';
      case 'completed':
        return 'text-primary-600 bg-primary-50';
      default:
        return 'text-neutral-600 bg-neutral-50';
    }
  };

  // Get priority color
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'border-danger-500 bg-danger-50';
      case 'high':
        return 'border-warning-500 bg-warning-50';
      case 'medium':
        return 'border-primary-500 bg-primary-50';
      case 'low':
        return 'border-neutral-300 bg-neutral-50';
      default:
        return 'border-neutral-300 bg-white';
    }
  };

  // Get event icon
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'document':
        return FileText;
      case 'appointment':
        return Calendar;
      case 'deadline':
        return Clock;
      case 'milestone':
        return Target;
      default:
        return FileText;
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-neutral-900 mb-2">
            Welcome back, Raj!
          </h1>
          <p className="text-neutral-600">
            You have {upcomingDeadlines} critical deadlines in the next 2 weeks
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="stat-card"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-primary-50 rounded-lg">
                <Target className="w-5 h-5 text-primary-600" />
              </div>
              <span className="text-sm text-success-600 font-medium">+12%</span>
            </div>
            <div className="stat-value">{Math.round(overallProgress)}%</div>
            <div className="stat-label">Overall Progress</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className="stat-card"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-warning-50 rounded-lg">
                <Clock className="w-5 h-5 text-warning-600" />
              </div>
              <span className="text-sm text-danger-600 font-medium">Urgent</span>
            </div>
            <div className="stat-value">{upcomingDeadlines}</div>
            <div className="stat-label">Critical Deadlines</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.2 }}
            className="stat-card"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-success-50 rounded-lg">
                <CheckCircle2 className="w-5 h-5 text-success-600" />
              </div>
              <span className="text-sm text-success-600 font-medium">On track</span>
            </div>
            <div className="stat-value">{completedTasks}/{totalTasks}</div>
            <div className="stat-label">Tasks Completed</div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, delay: 0.3 }}
            className="stat-card"
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-2 bg-secondary-50 rounded-lg">
                <Award className="w-5 h-5 text-secondary-600" />
              </div>
              <span className="text-sm text-primary-600 font-medium">Level 3</span>
            </div>
            <div className="stat-value">720</div>
            <div className="stat-label">Points Earned</div>
          </motion.div>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Plans & Timeline */}
          <div className="lg:col-span-2 space-y-8">
            {/* Active Plans */}
            <div className="card p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-neutral-900">Active Migration Plans</h2>
                <Link href="/migration/new" className="btn-secondary px-4 py-2 text-sm flex items-center">
                  <Plus className="w-4 h-4 mr-1" />
                  New Plan
                </Link>
              </div>

              <div className="space-y-4">
                {mockPlans.map((plan) => (
                  <div
                    key={plan.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      selectedPlan?.id === plan.id
                        ? 'border-primary-500 bg-primary-50/50'
                        : 'border-neutral-200 hover:border-primary-300'
                    }`}
                    onClick={() => setSelectedPlan(plan)}
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-semibold text-neutral-900">{plan.title}</h3>
                        <p className="text-sm text-neutral-600">
                          {plan.fromCountry} → {plan.toCountry}
                        </p>
                      </div>
                      <span className={`text-xs font-medium px-2 py-1 rounded-full ${getStatusColor(plan.status)}`}>
                        {plan.status.replace('-', ' ')}
                      </span>
                    </div>

                    <div className="mb-3">
                      <div className="flex justify-between text-sm text-neutral-600 mb-1">
                        <span>Phase {plan.currentPhase} of {plan.totalPhases}</span>
                        <span>{plan.progress}%</span>
                      </div>
                      <div className="progress-bar">
                        <div 
                          className="progress-fill"
                          style={{ width: `${plan.progress}%` }}
                        ></div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="text-sm">
                        <span className="text-neutral-600">Next deadline: </span>
                        <span className="font-medium text-neutral-900">
                          {plan.nextDeadline.title}
                        </span>
                      </div>
                      <div className="flex items-center text-sm">
                        {plan.nextDeadline.type === 'critical' && (
                          <AlertTriangle className="w-4 h-4 text-danger-500 mr-1" />
                        )}
                        <span className={plan.nextDeadline.type === 'critical' ? 'text-danger-600 font-medium' : 'text-neutral-600'}>
                          {differenceInDays(plan.nextDeadline.date, new Date())} days
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Timeline View with Tabs */}
            <div className="card p-6">
              <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-semibold text-neutral-900">Migration Hub</h2>
                {activeTab === 'timeline' && (
                  <button 
                    onClick={() => setShowAllEvents(!showAllEvents)}
                    className="text-sm text-primary-600 hover:text-primary-700"
                  >
                    {showAllEvents ? 'Show Less' : 'Show All'}
                  </button>
                )}
              </div>

              {/* Tab Navigation */}
              <div className="flex space-x-1 bg-neutral-100 p-1 rounded-lg mb-6">
                <button
                  onClick={() => setActiveTab('timeline')}
                  className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    activeTab === 'timeline'
                      ? 'bg-white text-primary-600 shadow-sm'
                      : 'text-neutral-600 hover:text-neutral-900'
                  }`}
                >
                  Timeline
                </button>
                <button
                  onClick={() => setActiveTab('news')}
                  className={`flex-1 px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                    activeTab === 'news'
                      ? 'bg-white text-primary-600 shadow-sm'
                      : 'text-neutral-600 hover:text-neutral-900'
                  }`}
                >
                  Latest News
                </button>
              </div>

              {/* Tab Content */}
              {activeTab === 'timeline' ? (
                <div className="space-y-4">
                  {mockTimeline.slice(0, showAllEvents ? undefined : 5).map((event, index) => (
                    <motion.div
                      key={event.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                      className={`flex items-start space-x-4 p-4 rounded-lg border-l-4 ${getPriorityColor(event.priority)}`}
                    >
                      <div className="flex-shrink-0">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          event.status === 'completed' 
                            ? 'bg-success-100 text-success-600'
                            : event.status === 'current'
                            ? 'bg-primary-100 text-primary-600'
                            : event.status === 'overdue'
                            ? 'bg-danger-100 text-danger-600'
                            : 'bg-neutral-100 text-neutral-600'
                        }`}>
                          {React.createElement(getEventIcon(event.type), { className: 'w-5 h-5' })}
                        </div>
                      </div>
                      
                      <div className="flex-grow">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-semibold text-neutral-900">{event.title}</h4>
                            <p className="text-sm text-neutral-600 mt-1">{event.description}</p>
                          </div>
                          <div className="text-right ml-4">
                            <p className="text-sm font-medium text-neutral-900">
                              {format(event.date, 'MMM dd, yyyy')}
                            </p>
                            {event.daysRemaining !== undefined && (
                              <p className={`text-xs mt-1 ${
                                event.daysRemaining <= 3 
                                  ? 'text-danger-600 font-medium' 
                                  : 'text-neutral-600'
                              }`}>
                                {event.daysRemaining === 0 
                                  ? 'Today' 
                                  : `${event.daysRemaining} days remaining`}
                              </p>
                            )}
                          </div>
                        </div>

                        {/* Links and Guide */}
                        {event.links && event.links.length > 0 && (
                          <div className="mt-2">
                            {event.links.map((link) => (
                              <a 
                                key={link.url}
                                href={link.url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-primary-600 hover:underline text-sm flex items-center"
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.403 1.403a2 2 0 01-2.827 0L15 17zm0 0V7m0 10l-4.586-4.586a2 2 0 00-2.828 0L4 15m11-8h6a2 2 0 012 2v6m-8-6H9a2 2 0 00-2 2v6" />
                                </svg>
                                {link.label}
                              </a>
                            ))}
                          </div>
                        )}
                        {event.guide && (
                          <p className="mt-2 text-sm text-neutral-500">
                            {event.guide}
                          </p>
                        )}
                      </div>
                    </motion.div>
                  ))}

                  <Link 
                    href="/timeline" 
                    className="mt-6 flex items-center justify-center text-primary-600 hover:text-primary-700 font-medium"
                  >
                    View Full Timeline
                    <ChevronRight className="w-4 h-4 ml-1" />
                  </Link>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <p className="text-sm text-neutral-600">
                      Latest migration news for Indian students moving to Germany
                    </p>
                  </div>
                  
                  {mockMigrationNews.map((news, index) => (
                    <motion.div
                      key={news.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.3, delay: index * 0.05 }}
                      className="flex items-start space-x-4 p-4 rounded-lg border border-neutral-200 hover:border-primary-300 hover:bg-primary-50/50 transition-all cursor-pointer"
                    >
                      <div className="flex-shrink-0">
                        <div className="w-10 h-10 rounded-full flex items-center justify-center bg-primary-100 text-primary-600">
                          <TrendingUp className="w-5 h-5" />
                        </div>
                      </div>
                      
                      <div className="flex-grow">
                        <h4 className="font-semibold text-neutral-900 mb-1">{news.headline}</h4>
                        <div className="flex items-center space-x-4 text-xs text-neutral-500">
                          <span>{news.source}</span>
                          <span>•</span>
                          <span>{format(news.date, 'MMM dd, yyyy')}</span>
                          <span>•</span>
                          <span className="text-primary-600 font-medium">{news.relevanceScore}% relevant</span>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Progress & Achievements */}
          <div className="space-y-8">
            {/* Progress Overview */}
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-neutral-900 mb-6">Progress Overview</h2>
              
              <div className="flex justify-center mb-6">
                <div style={{ width: 180, height: 180 }}>
                  <CircularProgressbar
                    value={selectedPlan?.progress || 0}
                    text={`${selectedPlan?.progress || 0}%`}
                    styles={buildStyles({
                      pathColor: `rgba(59, 130, 246, ${(selectedPlan?.progress || 0) / 100})`,
                      textColor: '#1e293b',
                      trailColor: '#f3f4f6',
                      textSize: '20px',
                    })}
                  />
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-600">Documents Uploaded</span>
                  <span className="font-medium text-neutral-900">7/10</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-600">Appointments Scheduled</span>
                  <span className="font-medium text-neutral-900">2/3</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-600">Requirements Met</span>
                  <span className="font-medium text-neutral-900">5/8</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-neutral-600">Days Until Target</span>
                  <span className="font-medium text-neutral-900">
                    {selectedPlan && differenceInDays(selectedPlan.targetDate, new Date())}
                  </span>
                </div>
              </div>
            </div>

            {/* Achievements */}
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-neutral-900 mb-6">Achievements</h2>
              
              <div className="space-y-4">
                {mockAchievements.map((achievement) => (
                  <div 
                    key={achievement.id}
                    className={`p-4 rounded-lg border ${
                      achievement.unlocked 
                        ? 'border-primary-200 bg-primary-50' 
                        : 'border-neutral-200 bg-neutral-50'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="text-2xl">{achievement.icon}</div>
                      <div className="flex-grow">
                        <h4 className={`font-semibold ${
                          achievement.unlocked ? 'text-neutral-900' : 'text-neutral-500'
                        }`}>
                          {achievement.title}
                        </h4>
                        <p className="text-sm text-neutral-600 mt-1">
                          {achievement.description}
                        </p>
                        <div className="mt-2">
                          <div className="flex justify-between text-xs text-neutral-600 mb-1">
                            <span>Progress</span>
                            <span>{achievement.progress}/{achievement.maxProgress}</span>
                          </div>
                          <div className="h-1.5 bg-neutral-200 rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full ${
                                achievement.unlocked 
                                  ? 'bg-primary-500' 
                                  : 'bg-neutral-400'
                              }`}
                              style={{ 
                                width: `${(achievement.progress / achievement.maxProgress) * 100}%` 
                              }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <button className="mt-6 w-full btn-outline py-2 text-sm">
                View All Achievements
              </button>
            </div>

            {/* Quick Actions */}
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-neutral-900 mb-4">Quick Actions</h2>
              <div className="space-y-2">
                <button className="w-full btn-secondary py-3 text-sm flex items-center justify-center">
                  <FileText className="w-4 h-4 mr-2" />
                  Upload Document
                </button>
                <button className="w-full btn-secondary py-3 text-sm flex items-center justify-center">
                  <Calendar className="w-4 h-4 mr-2" />
                  Schedule Appointment
                </button>
                <button className="w-full btn-secondary py-3 text-sm flex items-center justify-center">
                  <Users className="w-4 h-4 mr-2" />
                  Get Expert Help
                </button>
              </div>
            </div>

            {/* AI Chat Suggestions */}
            <div className="card p-6">
              <h2 className="text-xl font-semibold text-neutral-900 mb-4">Ask AI Assistant</h2>
              <div className="space-y-3">
                <p className="text-sm text-neutral-600 mb-4">
                  Get instant help with your migration questions
                </p>
                <div className="space-y-2">
                  <button 
                    onClick={() => updateContext({ 
                      ...context, 
                      suggestedQuestion: "What documents do I need for my German student visa?" 
                    })}
                    className="w-full text-left p-3 bg-blue-50 hover:bg-blue-100 rounded-lg text-sm text-blue-700 transition-colors"
                  >
                    "What documents do I need for my German student visa?"
                  </button>
                  <button 
                    onClick={() => updateContext({ 
                      ...context, 
                      suggestedQuestion: "How long does visa processing take?" 
                    })}
                    className="w-full text-left p-3 bg-green-50 hover:bg-green-100 rounded-lg text-sm text-green-700 transition-colors"
                  >
                    "How long does visa processing take?"
                  </button>
                  <button 
                    onClick={() => updateContext({ 
                      ...context, 
                      suggestedQuestion: "What are the financial requirements for Germany?" 
                    })}
                    className="w-full text-left p-3 bg-purple-50 hover:bg-purple-100 rounded-lg text-sm text-purple-700 transition-colors"
                  >
                    "What are the financial requirements for Germany?"
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

