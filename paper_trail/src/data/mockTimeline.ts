export interface TimelineEvent {
  id: string;
  title: string;
  description: string;
  date: Date;
  status: 'completed' | 'current' | 'upcoming' | 'overdue';
  type: 'document' | 'appointment' | 'deadline' | 'milestone';
  priority: 'critical' | 'high' | 'medium' | 'low';
  daysRemaining?: number;
  links?: { label: string; url: string }[];
  guide?: string;
  countryContext?: 'home' | 'destination';
}

export const mockTimeline: TimelineEvent[] = [
  {
    id: '1',
    title: 'Passport Renewal',
    description: 'Ensure passport is valid for at least 6 months',
    date: new Date('2025-01-15'),
    status: 'completed',
    type: 'document',
    priority: 'critical',
    links: [
      { label: 'Apply for Passport', url: 'https://passport.gov.in' },
      { label: 'Check Validity Rules', url: 'https://travel.state.gov/content/travel/en/passports.html' },
    ],
    guide: 'Gather necessary documents like old passport, address proof, and identity proof. Fill the online application form and schedule an appointment.',
    countryContext: 'home',
  },
  {
    id: '2',
    title: 'University Admission Letter',
    description: 'Receive official admission from TUM',
    date: new Date('2025-02-01'),
    status: 'completed',
    type: 'document',
    priority: 'critical',
    links: [
      { label: 'TUM Admissions', url: 'https://www.tum.de/en/studies/application-and-admission' },
    ],
    guide: 'Regularly check your application portal for updates. Once received, download and print the official letter.',
    countryContext: 'home',
  },
  {
    id: '3',
    title: 'Blocked Account Setup',
    description: 'Open blocked account with €11,208',
    date: new Date('2025-09-13'),
    status: 'current',
    type: 'deadline',
    priority: 'critical',
    daysRemaining: 5,
    links: [
      { label: 'Fintiba', url: 'https://www.fintiba.com/' },
      { label: 'Coracle', url: 'https://www.coracle.de/' },
    ],
    guide: 'Choose a blocked account provider, complete the online application, and transfer the required amount. Ensure you receive confirmation for visa application.',
    countryContext: 'home',
  },
  {
    id: '4',
    title: 'Health Insurance',
    description: 'Obtain German health insurance coverage',
    date: new Date('2025-09-18'),
    status: 'upcoming',
    type: 'document',
    priority: 'high',
    daysRemaining: 10,
    links: [
      { label: 'Mawista', url: 'https://www.mawista.com/en/' },
      { label: 'TK Health Insurance', url: 'https://www.tk.de/tk/english/739156' },
    ],
    guide: 'Research different providers and choose a plan that meets German visa requirements. Get a confirmation letter for your visa application.',
    countryContext: 'home',
  },
  {
    id: '5',
    title: 'Visa Appointment',
    description: 'Schedule appointment at German Consulate',
    date: new Date('2025-09-23'),
    status: 'upcoming',
    type: 'appointment',
    priority: 'critical',
    daysRemaining: 15,
    links: [
      { label: 'German Embassy/Consulate', url: 'https://www.india.diplo.de/in-en/service/visa' },
    ],
    guide: 'Book your appointment well in advance. Prepare all required documents as per the checklist provided by the consulate.',
    countryContext: 'home',
  },
  {
    id: '6',
    title: 'Flight Booking',
    description: 'Book one-way ticket to Munich',
    date: new Date('2025-10-08'),
    status: 'upcoming',
    type: 'appointment',
    priority: 'medium',
    daysRemaining: 30,
    links: [
      { label: 'Skyscanner', url: 'https://www.skyscanner.co.in/' },
      { label: 'Google Flights', url: 'https://www.google.com/flights' },
    ],
    guide: 'Look for flights after you have your visa. Consider flexible tickets if your plans might change.',
    countryContext: 'home',
  },
  {
    id: '7',
    title: 'Accommodation Search',
    description: 'Find and secure student housing',
    date: new Date('2025-10-23'),
    status: 'upcoming',
    type: 'milestone',
    priority: 'high',
    daysRemaining: 45,
    links: [
      { label: 'WG-Gesucht', url: 'https://www.wg-gesucht.de/en/' },
      { label: 'Studentenwerk München', url: 'https://www.studentenwerk-muenchen.de/en/accommodation/' },
    ],
    guide: 'Start your search early as student housing is competitive. Be wary of scams and try to view the place virtually if possible.',
    countryContext: 'destination',
  },
  {
    id: '8',
    title: 'Enrollment at University',
    description: 'Complete in-person enrollment at TUM',
    date: new Date('2025-11-07'),
    status: 'upcoming',
    type: 'milestone',
    priority: 'critical',
    daysRemaining: 60,
    links: [
      { label: 'TUM Enrollment Info', url: 'https://www.tum.de/en/studies/during-your-studies/organizing-your-studies/enrollment' },
    ],
    guide: 'Bring all original documents required for enrollment. This usually includes your admission letter, passport, visa, and health insurance proof.',
    countryContext: 'destination',
  },
  {
    id: '9',
    title: 'City Registration (Anmeldung)',
    description: 'Register your address with the local authorities',
    date: new Date('2025-11-12'),
    status: 'upcoming',
    type: 'document',
    priority: 'high',
    daysRemaining: 65,
    links: [
      { label: 'Munich City Registration', url: 'https://stadt.muenchen.de/rathaus/Stadtverwaltung/Kreisverwaltungsreferat/Buergerbuero/Wohnsitz-Meldeangelegenheiten.html' },
    ],
    guide: 'You must register your address within two weeks of moving into your accommodation. You will need your passport, visa, and landlord confirmation.',
    countryContext: 'destination',
  },
  {
    id: '10',
    title: 'Bank Account Opening',
    description: 'Open a regular student bank account',
    date: new Date('2025-11-17'),
    status: 'upcoming',
    type: 'appointment',
    priority: 'medium',
    daysRemaining: 70,
    links: [
      { label: 'N26', url: 'https://n26.com/en-de' },
      { label: 'Commerzbank', url: 'https://www.commerzbank.de/portal/en/privatkunden/privatkunden.html' },
    ],
    guide: 'Once you have your city registration, you can open a regular bank account. This is essential for daily expenses and receiving any stipends.',
    countryContext: 'destination',
  },
];