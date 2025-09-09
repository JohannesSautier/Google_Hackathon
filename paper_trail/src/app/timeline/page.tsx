// src/app/timeline/page.tsx
'use client';

import React from 'react';
import { mockTimeline } from '@/src/data/mockTimeline';
import { format } from 'date-fns';
import TimelineView from '@/components/timeline/timeline-view/TimelineView';

export default function TimelinePage() {
  const items = mockTimeline.map(event => ({
    ...event,
    date: new Date(event.date),
  }));

  return (
    <div className="w-full min-h-screen p-8 bg-gray-50">
      <h1 className="text-4xl font-bold text-gray-900 mb-8">Migration Timeline</h1>
      <div className="max-w-7xl mx-auto">
        <TimelineView items={items} />
      </div>
    </div>
  );
}
