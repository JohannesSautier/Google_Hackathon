import React, { useState, useEffect, useRef } from 'react';
import { format, isSameDay, isToday } from 'date-fns';
import {
  CheckCircleIcon as CheckCircle2,
  ClockIcon as Clock,
  FlagIcon as Flag,
  ChevronDownIcon as ChevronDown,
  ChevronUpIcon as ChevronUp,
  PlayIcon as Play,
  PauseIcon as Pause,
  ArrowTopRightOnSquareIcon as ExternalLink,
} from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '@/components/ui/button/Button';
import { TimelineEvent } from '@/src/data/mockTimeline'; // Import TimelineEvent

interface TimelineViewProps {
  items: TimelineEvent[];
}

const CalendarDay: React.FC<{ date: Date; isEventDay: boolean; isCurrent: boolean; countryContext?: 'home' | 'destination' }>
  = ({ date, isEventDay, isCurrent, countryContext }) => {
    const day = format(date, 'd');
    const month = format(date, 'MMM');
    const isTodayDay = isToday(date);

    return (
      <div className={`flex flex-col items-center justify-center p-1 rounded-md text-xs font-medium
        ${isCurrent ? 'bg-blue-500 text-white' : isEventDay ? 'bg-blue-100 text-blue-800' : 'bg-gray-50 text-gray-600'}
        ${isTodayDay && !isCurrent ? 'border-2 border-red-500' : ''}
        relative overflow-hidden
      `}>
        <span className="text-[0.6rem] uppercase">{month}</span>
        <span className="text-lg font-bold leading-none">{day}</span>
      </div>
    );
  };

export default function TimelineView({ items }: TimelineViewProps) {
  const [expandedItem, setExpandedItem] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  const itemRefs = useRef<(HTMLDivElement | null)[]>([]);
  const timelineRef = useRef<HTMLDivElement>(null);

  const sortedItems = [...items].sort((a, b) => a.date.getTime() - b.date.getTime());

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying && currentIndex < sortedItems.length) {
      interval = setInterval(() => {
        setCurrentIndex((prevIndex) => {
          const nextIndex = prevIndex + 1;
          if (nextIndex < sortedItems.length) {
            setExpandedItem(sortedItems[nextIndex]?.id || null);
            itemRefs.current[nextIndex]?.scrollIntoView({
              behavior: 'smooth',
              inline: 'center',
            });
          }
          return nextIndex;
        });
      }, 2000); // Advance every 2 seconds
    } else if (currentIndex >= sortedItems.length) {
      setIsPlaying(false);
      setCurrentIndex(0); // Reset after playing all items
      setExpandedItem(null);
    }
    return () => clearInterval(interval);
  }, [isPlaying, currentIndex, sortedItems.length, sortedItems]);

  const toggleExpand = (id: string) => {
    setExpandedItem(expandedItem === id ? null : id);
  };

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
    if (!isPlaying && currentIndex === 0 && sortedItems.length > 0) {
      setExpandedItem(sortedItems[0]?.id || null);
      itemRefs.current[0]?.scrollIntoView({
        behavior: 'smooth',
        inline: 'center',
      });
    }
  };

  const resetTimeline = () => {
    setIsPlaying(false);
    setCurrentIndex(0);
    setExpandedItem(null);
    itemRefs.current[0]?.scrollIntoView({
      behavior: 'smooth',
      inline: 'start',
    });
  };

  return (
    <div className="w-full">
      {/* Play/Reset Controls */}
      <div className="sticky top-0 bg-gray-50 z-10 py-4 flex justify-center items-center mb-8 space-x-4">
        <Button onClick={togglePlay} className="flex items-center">
          {isPlaying ? <Pause className="mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4" />}
          {isPlaying ? 'Pause' : 'Play'}
        </Button>
        <Button onClick={resetTimeline} variant="outline">Reset</Button>
      </div>

      <div ref={timelineRef} className="relative flex overflow-x-auto pb-4 scrollbar-hide">
        {/* Horizontal line */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gray-200"></div>

        {sortedItems.map((event, index) => (
          <div
            key={event.id}
            ref={(el) => {
              itemRefs.current[index] = el;
            }}
            className="flex-shrink-0 w-64 mx-6 relative pt-20 pb-4"
          >
            {/* Calendar Day */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 z-10">
              <CalendarDay
                date={event.date}
                isEventDay={true}
                isCurrent={index === currentIndex && isPlaying}
                countryContext={event.countryContext}
              />
            </div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`bg-white p-4 border rounded-lg shadow-sm w-full cursor-pointer mt-4
                ${expandedItem === event.id ? 'border-blue-400' : 'border-gray-200'}
                ${index === currentIndex && isPlaying ? 'ring-4 ring-blue-300' : ''}
              `}
              onClick={() => toggleExpand(event.id)}
            >
              <div className="flex items-center justify-between mb-2">
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusClasses(event.status)}`}>
                  {event.status.charAt(0).toUpperCase() + event.status.slice(1)}
                </span>
                <span className="text-sm text-gray-500 flex items-center">
                  {getTypeIcon(event.type)}
                  <span className="ml-1">{format(event.date, 'MMM dd, yyyy')}</span>
                  {expandedItem === event.id ? <ChevronUp className="ml-2 h-4 w-4" /> : <ChevronDown className="ml-2 h-4 w-4" />}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-1">{event.title}</h3>
              <p className="text-gray-600 text-sm">{event.description}</p>
              {event.daysRemaining !== undefined && event.status !== 'completed' && (
                <p className="text-sm text-blue-600 mt-2">
                  {event.daysRemaining} days remaining
                </p>
              )}

              <AnimatePresence>
                {expandedItem === event.id && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                    className="mt-4 pt-4 border-t border-gray-200"
                  >
                    {event.guide && (
                      <div className="mb-4">
                        <h4 className="font-semibold text-gray-800">Guide:</h4>
                        <p className="text-gray-700 text-sm mt-1">{event.guide}</p>
                      </div>
                    )}
                    {event.links && event.links.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-800">Useful Links:</h4>
                        <ul className="mt-1 space-y-1">
                          {event.links.map((link, linkIndex) => (
                            <li key={linkIndex}>
                              <a href={link.url} target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline flex items-center text-sm">
                                {link.label} <ExternalLink className="ml-1 h-3 w-3" />
                              </a>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>
        ))}
      </div>
    </div>
  );
}

function getStatusClasses(status: string) {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'current':
      return 'bg-blue-100 text-blue-800';
    case 'upcoming':
      return 'bg-yellow-100 text-yellow-800';
    case 'overdue':
      return 'bg-red-100 text-red-800';
    default:
      return '';
  }
}

function getPriorityClasses(priority: string) {
  switch (priority) {
    case 'critical':
      return 'bg-red-500';
    case 'high':
      return 'bg-orange-500';
    case 'medium':
      return 'bg-yellow-500';
    case 'low':
      return 'bg-green-500';
    default:
      return '';
  }
}

function getTypeIcon(type: string) {
  switch (type) {
    case 'document':
      return <Flag className="w-4 h-4 text-gray-400" />;
    case 'appointment':
      return <Clock className="w-4 h-4 text-gray-400" />;
    case 'deadline':
      return <Flag className="w-4 h-4 text-gray-400" />;
    case 'milestone':
      return <CheckCircle2 className="w-4 h-4 text-gray-400" />;
    default:
      return null;
  }
}
