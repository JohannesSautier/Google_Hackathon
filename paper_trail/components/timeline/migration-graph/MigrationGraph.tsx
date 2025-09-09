import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { format, parseISO, differenceInDays } from 'date-fns';
import { Button } from '@/components/ui/button/Button';
import { PlayIcon as Play, PauseIcon as Pause } from '@heroicons/react/24/outline';

interface TimelineEvent {
  id: string;
  title: string;
  description: string;
  date: Date;
  status: 'completed' | 'current' | 'upcoming' | 'overdue';
  type: 'document' | 'appointment' | 'deadline' | 'milestone';
  priority: 'critical' | 'high' | 'medium' | 'low';
  daysRemaining?: number;
}

interface MigrationGraphProps {
  items: TimelineEvent[];
}

const MigrationGraph: React.FC<MigrationGraphProps> = ({ items }) => {
  const sortedItems = [...items].sort((a, b) => a.date.getTime() - b.date.getTime());

  const processData = (currentIndex: number) => {
    let completedCount = 0;
    const totalTasks = sortedItems.length;

    return sortedItems.map((event, index) => {
      if (index <= currentIndex && event.status === 'completed') {
        completedCount++;
      }
      const completionPercentage = totalTasks > 0 ? (completedCount / totalTasks) * 100 : 0;
      return {
        name: format(event.date, 'MMM dd'),
        date: event.date,
        completion: parseFloat(completionPercentage.toFixed(2)),
        title: event.title,
        description: event.description,
        status: event.status,
      };
    });
  };

  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [graphData, setGraphData] = useState(processData(0));

  useEffect(() => {
    setGraphData(processData(currentStep));
  }, [currentStep, items]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isPlaying && currentStep < sortedItems.length - 1) {
      interval = setInterval(() => {
        setCurrentStep((prevStep) => prevStep + 1);
      }, 1000); // Advance every 1 second
    } else if (currentStep === sortedItems.length - 1) {
      setIsPlaying(false);
    }
    return () => clearInterval(interval);
  }, [isPlaying, currentStep, sortedItems.length]);

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  const resetGraph = () => {
    setCurrentStep(0);
    setIsPlaying(false);
  };

  return (
    <div className="w-full">
      <div className="flex justify-center items-center mb-4 space-x-2">
        <Button onClick={togglePlay} className="flex items-center">
          {isPlaying ? <Pause className="mr-2 h-4 w-4" /> : <Play className="mr-2 h-4 w-4" />}
          {isPlaying ? 'Pause' : 'Play'}
        </Button>
        <Button onClick={resetGraph} variant="outline">Reset</Button>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart
          data={graphData}
          margin={{
            top: 20, right: 30, left: 20, bottom: 5,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="completion" fill="#8884d8" />
        </BarChart>
      </ResponsiveContainer>
      <div className="mt-4 p-4 bg-white rounded-lg shadow-sm">
        <h3 className="text-lg font-semibold text-gray-900">Current Event: {graphData[currentStep]?.title || 'N/A'}</h3>
        <p className="text-gray-600 text-sm">{graphData[currentStep]?.description || 'Select an event to see details.'}</p>
        {graphData[currentStep]?.status && (
          <p className="text-sm text-gray-500 mt-2">Status: {graphData[currentStep].status}</p>
        )}
      </div>
    </div>
  );
};

export default MigrationGraph;
