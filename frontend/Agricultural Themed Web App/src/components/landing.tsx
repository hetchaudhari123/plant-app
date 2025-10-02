import { Link } from 'react-router-dom';
import { Upload, Zap, Shield, BarChart3, ArrowRight, Camera, Leaf, Users, Image } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { ImageWithFallback } from './figma/ImageWithFallback';

export function Landing() {
  const features = [
    {
      icon: Image,
      title: 'AI-Powered Analysis',
      description: 'Upload crop images and get instant disease detection with 99% accuracy'
    },
    {
      icon: Zap,
      title: 'Real-time Results',
      description: 'Get analysis results in seconds, not days'
    },
    {
      icon: Shield,
      title: 'Preventive Care',
      description: 'Early detection helps prevent crop loss and increases yield'
    },
    // {
    //   icon: BarChart3,
    //   title: 'Detailed Reports',
    //   description: 'Comprehensive analysis with treatment recommendations'
    // }
  ];

  const stats = [
    { number: '5', label: 'AI Models' },
    { number: '99%', label: 'Accuracy Rate' },
    { number: '54', label: 'Crop Diseases Detected' },
    // { number: '24/7', label: 'Support' }
  ];

  return (
    <div className="space-y-20">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div className="space-y-8">
              <div className="space-y-4">
                <div className="inline-flex items-center space-x-2 bg-green-100 text-green-800 px-4 py-2 rounded-full">
                  <Leaf className="h-4 w-4" />
                  <span className="text-sm">Smart Agriculture</span>
                </div>
                <h1 className="text-4xl lg:text-6xl text-gray-900 leading-tight">
                  Protect Your Crops with {' '}
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-green-600 to-green-400">
                    AI Vision
                  </span>
                </h1>
                <p className="text-xl text-gray-600 leading-relaxed">
                  Upload images of your crops and get instant disease detection.
                </p>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <Link to="/upload">
                  <Button size="lg" className="bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 shadow-lg">
                    <Upload className="h-5 w-5 mr-2" />
                    Upload Image
                  </Button>
                </Link>
                <Link to="/login">
                  <Button size="lg" variant="outline" className="border-green-300 text-green-700 hover:bg-green-50">
                    Get Started
                    <ArrowRight className="h-5 w-5 ml-2" />
                  </Button>
                </Link>
              </div>
            </div>
            
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-green-400 to-green-600 rounded-2xl transform rotate-3 opacity-20"></div>
              <ImageWithFallback
                src="https://images.unsplash.com/photo-1630277975641-38748ee8f41a?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxhZ3JpY3VsdHVyZSUyMGZhcm0lMjBmaWVsZCUyMGNyb3BzfGVufDF8fHx8MTc1ODg4Mzc4MHww&ixlib=rb-4.1.0&q=80&w=1080"
                alt="Agricultural field with healthy crops"
                className="relative rounded-2xl shadow-2xl w-full h-96 object-cover"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl text-gray-900 mb-4">
              Why Choose AgriVision?
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Advanced AI technology meets agricultural expertise to give you the tools you need for successful farming.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <Card key={index} className="border-green-100 hover:shadow-lg transition-shadow duration-300">
                  <CardContent className="p-6 text-center">
                    <div className="bg-gradient-to-r from-green-500 to-green-400 w-12 h-12 rounded-lg flex items-center justify-center mx-auto mb-4">
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <h3 className="text-lg text-gray-900 mb-2">{feature.title}</h3>
                    <p className="text-gray-600">{feature.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-20 bg-gradient-to-r from-green-600 to-green-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl lg:text-4xl text-white mb-2">{stat.number}</div>
                <div className="text-green-100">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl lg:text-4xl text-gray-900 mb-4">
              How It Works
            </h2>
            <p className="text-xl text-gray-600">
              Simple, fast, and accurate crop analysis in three easy steps
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="bg-gradient-to-r from-green-500 to-green-400 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Upload className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl text-gray-900 mb-2">Upload Image</h3>
              <p className="text-gray-600">
                Upload a photo of your crop
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-gradient-to-r from-green-500 to-green-400 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <Zap className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl text-gray-900 mb-2">AI Analysis</h3>
              <p className="text-gray-600">
                Our advanced AI analyzes your image for diseases, pests, and nutrient deficiencies
              </p>
            </div>
            
            <div className="text-center">
              <div className="bg-gradient-to-r from-green-500 to-green-400 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
                <BarChart3 className="h-8 w-8 text-white" />
              </div>
              <h3 className="text-xl text-gray-900 mb-2">Get Results</h3>
              <p className="text-gray-600">
                Get instant plant disease predictions from your images
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-green-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="max-w-3xl mx-auto">
            <Users className="h-16 w-16 text-green-600 mx-auto mb-6" />
            <h2 className="text-3xl lg:text-4xl text-gray-900 mb-4">
              Know Your Plant’s Health Instantly
            </h2>
            <p className="text-xl text-gray-600 mb-8">
              Start protecting your crops today with AI-powered agricultural insights.
            </p>
            <Link to="/login">
              <Button size="lg" className="bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 shadow-lg">
                Start Free Trial
                <ArrowRight className="h-5 w-5 ml-2" />
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}