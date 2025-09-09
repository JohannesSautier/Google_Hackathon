'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  ArrowRightIcon as ArrowRight, 
  CalendarIcon as Calendar, 
  ClockIcon as Clock, 
  GlobeAltIcon as Globe, 
  ShieldCheckIcon as Shield, 
  CheckCircleIcon as CheckCircle, 
  CloudIcon as Cloud, 
  SparklesIcon as Sparkles,
  MapPinIcon as MapPin,
  BriefcaseIcon as Briefcase,
  AcademicCapIcon as GraduationCap,
  HeartIcon as Heart,
  BuildingOfficeIcon as Building
} from '@heroicons/react/24/outline';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

// Country and city data
const COUNTRIES = [
	{ code: 'IN', name: 'India', flag: '🇮🇳', cities: ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Kolkata', 'Hyderabad', 'Pune', 'Ahmedabad'] },
	{ code: 'US', name: 'United States', flag: '🇺🇸', cities: ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix', 'Philadelphia', 'San Antonio', 'San Diego'] },
	{ code: 'UK', name: 'United Kingdom', flag: '🇬🇧', cities: ['London', 'Manchester', 'Birmingham', 'Leeds', 'Glasgow', 'Edinburgh', 'Liverpool', 'Bristol'] },
	{ code: 'DE', name: 'Germany', flag: '🇩🇪', cities: ['Berlin', 'Munich', 'Hamburg', 'Frankfurt', 'Cologne', 'Stuttgart', 'Düsseldorf', 'Dortmund'] },
	{ code: 'CA', name: 'Canada', flag: '🇨🇦', cities: ['Toronto', 'Vancouver', 'Montreal', 'Calgary', 'Edmonton', 'Ottawa', 'Winnipeg', 'Quebec City'] },
	{ code: 'AU', name: 'Australia', flag: '🇦🇺', cities: ['Sydney', 'Melbourne', 'Brisbane', 'Perth', 'Adelaide', 'Gold Coast', 'Newcastle', 'Canberra'] },
	{ code: 'FR', name: 'France', flag: '🇫🇷', cities: ['Paris', 'Marseille', 'Lyon', 'Toulouse', 'Nice', 'Nantes', 'Strasbourg', 'Montpellier'] },
	{ code: 'NL', name: 'Netherlands', flag: '🇳🇱', cities: ['Amsterdam', 'Rotterdam', 'The Hague', 'Utrecht', 'Eindhoven', 'Tilburg', 'Groningen', 'Almere'] },
	{ code: 'CH', name: 'Switzerland', flag: '🇨🇭', cities: ['Zurich', 'Geneva', 'Basel', 'Bern', 'Lausanne', 'St. Gallen', 'Lucerne', 'Lugano'] },
	{ code: 'SG', name: 'Singapore', flag: '🇸🇬', cities: ['Singapore City', 'Jurong East', 'Tampines', 'Woodlands', 'Sengkang', 'Punggol', 'Yishun', 'Ang Mo Kio'] },
	{ code: 'JP', name: 'Japan', flag: '🇯🇵', cities: ['Tokyo', 'Osaka', 'Kyoto', 'Yokohama', 'Nagoya', 'Sapporo', 'Fukuoka', 'Kobe'] },
	{ code: 'AE', name: 'UAE', flag: '🇦🇪', cities: ['Dubai', 'Abu Dhabi', 'Sharjah', 'Ajman', 'Ras Al Khaimah', 'Fujairah', 'Umm Al Quwain'] },
];

const PURPOSE_OPTIONS = [
	{ value: 'work', label: 'Employment', icon: Briefcase, description: 'Work visa, job relocation' },
	{ value: 'study', label: 'Education', icon: GraduationCap, description: 'Student visa, academic programs' },
	{ value: 'family', label: 'Family Reunion', icon: Heart, description: 'Spouse, dependent visas' },
	{ value: 'business', label: 'Business/Investment', icon: Building, description: 'Entrepreneur, investor visas' },
];

export default function LandingPage() {
	const router = useRouter();
	const [formData, setFormData] = useState({
		originCountry: '',
		originCity: '',
		destinationCountry: '',
		destinationCity: '',
		purpose: '',
		timeline: '',
	});

	const stats = [
		{ value: '10,000+', label: 'Successful Migrations', trend: '+23%' },
		{ value: '50+', label: 'Countries Covered', trend: 'Global' },
		{ value: '99.2%', label: 'On-Time Success Rate', trend: '+5%' },
		{ value: '24/7', label: 'AI Assistance', trend: 'Always' },
	];

	const features = [
		{
			icon: Calendar,
			title: 'Smart Timeline Management',
			description:
				'Never miss a deadline with our intelligent scheduling system that tracks every document, appointment, and requirement.',
			color: 'text-blue-500',
			bgColor: 'bg-blue-50',
		},
		{
			icon: Globe,
			title: 'Country-Specific Guidance',
			description:
				'Get tailored advice for your specific migration route with up-to-date regulations and requirements.',
			color: 'text-green-500',
			bgColor: 'bg-green-50',
		},
		{
			icon: Shield,
			title: 'Document Verification',
			description:
				'Ensure all your documents meet requirements with our AI-powered verification system.',
			color: 'text-purple-500',
			bgColor: 'bg-purple-50',
		},
		{
			icon: Clock,
			title: 'Real-time Updates',
			description:
				'Stay informed with instant notifications about policy changes and deadline reminders.',
			color: 'text-orange-500',
			bgColor: 'bg-orange-50',
		},
	];

	const handleInputChange = (field: string, value: string) => {
		setFormData(prev => {
			const newData = { ...prev, [field]: value };
			
			// Reset city when country changes
			if (field === 'originCountry') {
				newData.originCity = '';
			} else if (field === 'destinationCountry') {
				newData.destinationCity = '';
			}
			
			return newData;
		});
	};

	const handleStartPlanning = () => {
		// Validate required fields
		const requiredFields = ['originCountry', 'destinationCountry', 'purpose', 'timeline'];
		const isFormValid = requiredFields.every(field => formData[field as keyof typeof formData]);
		
		if (isFormValid) {
			// Store the structured data
			const migrationContext = {
				originCountry: formData.originCountry,
				originCity: formData.originCity,
				destinationCountry: formData.destinationCountry,
				destinationCity: formData.destinationCity,
				purpose: formData.purpose,
				timeline: formData.timeline,
			};
			
			sessionStorage.setItem('migrationContext', JSON.stringify(migrationContext));
			router.push('/migration/verify');
		}
	};

	const isFormValid = formData.originCountry && formData.destinationCountry && formData.purpose && formData.timeline;

	return (
		<div className="min-h-screen bg-white">
			{/* Hero Section */}
			<section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
				<div className="max-w-7xl mx-auto">
					<motion.div
						initial={{ opacity: 0, y: 20 }}
						animate={{ opacity: 1, y: 0 }}
						transition={{ duration: 0.6 }}
						className="text-center"
					>
						<h1 className="text-5xl sm:text-6xl font-bold text-gray-900 mb-6">
							Your Immigration Journey,
							<span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
								{' '}
								Simplified
							</span>
						</h1>
						<p className="text-xl text-gray-600 mb-12 max-w-3xl mx-auto">
							Never miss a deadline. Track every step. Get AI-powered guidance for your immigration process.
						</p>

						{/* Migration Planning Form */}
						<div className="max-w-4xl mx-auto mb-16">
							<div className="relative">
								<div className="absolute inset-0 bg-gradient-to-r from-blue-100 to-purple-100 rounded-2xl blur-xl opacity-50"></div>
								<div className="relative bg-white rounded-2xl shadow-xl border border-gray-200 p-8">
									<div className="text-center mb-8">
										<h2 className="text-2xl font-bold text-gray-900 mb-2">
											Plan Your Migration Journey
										</h2>
										<p className="text-gray-600">
											Tell us about your migration details to get started
										</p>
									</div>

									{/* Country and City Selection */}
									<div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
										{/* Origin Country & City */}
										<div className="space-y-4">
											<div>
												<label className="block text-sm font-medium text-gray-700 mb-2">
													<MapPin className="w-4 h-4 inline mr-1" />
													From Country
												</label>
												<select
													value={formData.originCountry}
													onChange={(e) => handleInputChange('originCountry', e.target.value)}
													className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
												>
													<option value="">Select your current country</option>
													{COUNTRIES.map((country) => (
														<option key={country.code} value={country.code}>
															{country.flag} {country.name}
														</option>
													))}
												</select>
											</div>
											
											{formData.originCountry && (
												<div>
													<label className="block text-sm font-medium text-gray-700 mb-2">
														City
													</label>
													<select
														value={formData.originCity}
														onChange={(e) => handleInputChange('originCity', e.target.value)}
														className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
													>
														<option value="">Select your city</option>
														{COUNTRIES.find(c => c.code === formData.originCountry)?.cities.map((city) => (
															<option key={city} value={city}>
																{city}
															</option>
														))}
													</select>
												</div>
											)}
										</div>

										{/* Destination Country & City */}
										<div className="space-y-4">
											<div>
												<label className="block text-sm font-medium text-gray-700 mb-2">
													<MapPin className="w-4 h-4 inline mr-1" />
													To Country
												</label>
												<select
													value={formData.destinationCountry}
													onChange={(e) => handleInputChange('destinationCountry', e.target.value)}
													className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
												>
													<option value="">Select your destination country</option>
													{COUNTRIES.filter(c => c.code !== formData.originCountry).map((country) => (
														<option key={country.code} value={country.code}>
															{country.flag} {country.name}
														</option>
													))}
												</select>
											</div>
											
											{formData.destinationCountry && (
												<div>
													<label className="block text-sm font-medium text-gray-700 mb-2">
														City
													</label>
													<select
														value={formData.destinationCity}
														onChange={(e) => handleInputChange('destinationCity', e.target.value)}
														className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
													>
														<option value="">Select your destination city</option>
														{COUNTRIES.find(c => c.code === formData.destinationCountry)?.cities.map((city) => (
															<option key={city} value={city}>
																{city}
															</option>
														))}
													</select>
												</div>
											)}
										</div>
									</div>

									{/* Purpose Selection */}
									<div className="mb-6">
										<label className="block text-sm font-medium text-gray-700 mb-3">
											Purpose of Migration
										</label>
										<div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
											{PURPOSE_OPTIONS.map((purpose) => (
												<button
													key={purpose.value}
													onClick={() => handleInputChange('purpose', purpose.value)}
													className={`p-4 rounded-lg border-2 text-left transition-all ${
														formData.purpose === purpose.value
															? 'border-blue-500 bg-blue-50'
															: 'border-gray-200 hover:border-blue-300'
													}`}
												>
													<div className="flex items-center space-x-3">
														<div className="p-2 bg-white rounded-lg">
															<purpose.icon className="w-5 h-5 text-blue-600" />
														</div>
														<div>
															<h3 className="font-semibold text-gray-900">{purpose.label}</h3>
															<p className="text-sm text-gray-600">{purpose.description}</p>
														</div>
													</div>
												</button>
											))}
										</div>
									</div>

									{/* Timeline Selection */}
									<div className="mb-6">
										<label className="block text-sm font-medium text-gray-700 mb-3">
											<Clock className="w-4 h-4 inline mr-1" />
											When do you plan to migrate?
										</label>
										<div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
											{['ASAP', '1-3 months', '3-6 months', '6+ months'].map((timeline) => (
												<button
													key={timeline}
													onClick={() => handleInputChange('timeline', timeline)}
													className={`py-3 px-4 rounded-lg border-2 transition-all ${
														formData.timeline === timeline
															? 'border-blue-500 bg-blue-50 text-blue-700'
															: 'border-gray-200 hover:border-blue-300'
													}`}
												>
													<Clock className="w-4 h-4 mx-auto mb-1" />
													<div className="text-sm font-medium">{timeline}</div>
												</button>
											))}
										</div>
									</div>

									<div className="flex justify-between items-center">
										<div className="flex items-center space-x-4 text-sm text-gray-500">
											<span className="flex items-center">
												<CheckCircle className="w-4 h-4 mr-1 text-green-500" />
												AI-Powered Analysis
											</span>
											<span className="flex items-center">
												<Shield className="w-4 h-4 mr-1 text-blue-500" />
												Secure & Private
											</span>
										</div>
										<button
											onClick={handleStartPlanning}
											disabled={!isFormValid}
											className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-3 rounded-lg flex items-center space-x-2 font-medium transition"
										>
											<span>Start Planning</span>
											<ArrowRight className="w-4 h-4" />
										</button>
									</div>
									<div className="mt-4 text-center text-xs text-gray-400 flex items-center justify-center space-x-2">
										<span>Powered by</span>
										<div className="flex items-center space-x-1">
											<Cloud className="w-4 h-4 text-blue-400" />
											<span className="font-semibold text-gray-500">Google Cloud</span>
										</div>
										<span>&</span>
										<div className="flex items-center space-x-1">
											<Sparkles className="w-4 h-4 text-purple-400" />
											<span className="font-semibold text-gray-500">Gemini</span>
										</div>
									</div>
								</div>
							</div>
						</div>

						{/* Stats Grid */}
						<div className="grid grid-cols-2 sm:grid-cols-4 gap-6 mb-20">
							{stats.map((stat, index) => (
								<motion.div
									key={index}
									initial={{ opacity: 0, y: 20 }}
									animate={{ opacity: 1, y: 0 }}
									transition={{ duration: 0.6, delay: index * 0.1 }}
									className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm"
								>
									<div className="text-3xl font-bold text-gray-900">{stat.value}</div>
									<div className="text-sm text-gray-500 mt-1">{stat.label}</div>
									<div className="text-sm text-green-600 mt-2">
										<span>{stat.trend}</span>
									</div>
								</motion.div>
							))}
						</div>
					</motion.div>
				</div>
			</section>

			{/* Features Section */}
			<section className="py-20 bg-gray-50">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
					<div className="text-center mb-16">
						<h2 className="text-4xl font-bold text-gray-900 mb-4">
							Everything You Need for a Successful Migration
						</h2>
						<p className="text-xl text-gray-600 max-w-3xl mx-auto">
							Our comprehensive platform ensures you never miss a step in your immigration journey
						</p>
					</div>

					<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
						{features.map((feature, index) => (
							<motion.div
								key={index}
								initial={{ opacity: 0, y: 20 }}
								whileInView={{ opacity: 1, y: 0 }}
								transition={{ duration: 0.6, delay: index * 0.1 }}
								viewport={{ once: true }}
								className="bg-white rounded-xl p-6 border border-gray-200 hover:shadow-lg transition-shadow"
							>
								<div
									className={`${feature.bgColor} w-12 h-12 rounded-lg flex items-center justify-center mb-4`}
								>
									<feature.icon className={`w-6 h-6 ${feature.color}`} />
								</div>
								<h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
								<p className="text-gray-600">{feature.description}</p>
							</motion.div>
						))}
					</div>
				</div>
			</section>

			{/* CTA Section */}
			<section className="py-20 bg-gradient-to-r from-blue-50 to-purple-50">
				<div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
					<h2 className="text-4xl font-bold text-gray-900 mb-6">
						Ready to Start Your Migration Journey?
					</h2>
					<p className="text-xl text-gray-600 mb-8">
						Join thousands who have successfully migrated with our intelligent planning system
					</p>
					<div className="flex justify-center space-x-4">
						<button className="bg-blue-500 hover:bg-blue-600 text-white px-8 py-3 rounded-lg font-medium transition">
							Get Started Free
						</button>
						<button className="border border-gray-300 hover:border-gray-400 text-gray-700 px-8 py-3 rounded-lg font-medium transition">
							View Demo
						</button>
					</div>
				</div>
			</section>

			{/* Footer */}
			<footer className="bg-gray-900 text-white py-12">
				<div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
					<div className="grid md:grid-cols-4 gap-8">
						<div>
							<div className="flex items-center space-x-2 mb-4">
								<div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg"></div>
								<span className="text-xl font-bold">PaperTrail</span>
							</div>
							<p className="text-gray-400">Making immigration simple, one step at a time.</p>
						</div>
						<div>
							<h4 className="font-semibold mb-4">Product</h4>
							<ul className="space-y-2 text-gray-400">
								<li>
									<a href="#" className="hover:text-white transition">
										Features
									</a>
								</li>
								<li>
									<a href="#" className="hover:text-white transition">
										Pricing
									</a>
								</li>
								<li>
									<a href="#" className="hover:text-white transition">
										Demo
									</a>
								</li>
							</ul>
						</div>
						<div>
							<h4 className="font-semibold mb-4">Support</h4>
							<ul className="space-y-2 text-gray-400">
								<li>
									<a href="#" className="hover:text-white transition">
										Help Center
									</a>
								</li>
								<li>
									<a href="#" className="hover:text-white transition">
										Contact
									</a>
								</li>
								<li>
									<a href="#" className="hover:text-white transition">
										Privacy
									</a>
								</li>
							</ul>
						</div>
						<div>
							<h4 className="font-semibold mb-4">Company</h4>
							<ul className="space-y-2 text-gray-400">
								<li>
									<a href="#" className="hover:text-white transition">
										About
									</a>
								</li>
								<li>
									<a href="#" className="hover:text-white transition">
										Blog
									</a>
								</li>
								<li>
									<a href="#" className="hover:text-white transition">
										Careers
									</a>
								</li>
							</ul>
						</div>
					</div>
					<div className="border-t border-gray-800 mt-12 pt-8 text-center text-gray-400">
						<p>&copy; 2024 PaperTrail. All rights reserved.</p>
					</div>
				</div>
			</footer>
		</div>
	);
}
