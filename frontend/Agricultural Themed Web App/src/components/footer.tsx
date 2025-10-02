import { Link } from 'react-router-dom';
import { Leaf, Mail, Phone, MapPin } from 'lucide-react';

export function Footer() {
  return (
   <footer className="bg-green-800 text-green-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="py-12">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12 lg:gap-16 items-start">
            {/* Brand */}
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <div className="bg-gradient-to-r from-green-500 to-green-400 p-2 rounded-lg">
                  <Leaf className="h-6 w-6 text-white" />
                </div>
                <span className="text-xl text-white">AgriVision</span>
              </div>
              <p className="text-green-200 mb-4 max-w-md">
                Advanced agricultural image analysis powered by AI. Helping farmers make informed decisions 
                for healthier crops and better yields.
              </p>
              <div className="flex space-x-4">
                
              </div>
            </div>

            {/* Quick Links */}
            <div className="md:ml-auto">
              <h3 className="text-white mb-4">Quick Links</h3>
              <ul className="space-y-2">
                <li>
                  <Link to="/" className="text-green-200 hover:text-white transition-colors">
                    Home
                  </Link>
                </li>
                <li>
                  <Link to="/upload" className="text-green-200 hover:text-white transition-colors">
                    Upload Image
                  </Link>
                </li>
                <li>
                  <Link to="/history" className="text-green-200 hover:text-white transition-colors">
                    Analysis History
                  </Link>
                </li>
                <li>
                  <Link to="/profile" className="text-green-200 hover:text-white transition-colors">
                    Profile
                  </Link>
                </li>
              </ul>
            </div>

            
          </div>
        </div>

        <div className="border-t border-green-700 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <p className="text-green-200 text-sm">
              © 2025 AgriVision. All rights reserved.
            </p>
            
          </div>
        </div>
      </div>
    </footer>
  );
}