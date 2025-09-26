import { useState } from 'react';
import { Calendar, Download, Filter, Search, Eye, Trash2, MoreVertical } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../ui/dropdown-menu';
import { ImageWithFallback } from '../figma/ImageWithFallback';

interface HistoryItem {
  id: string;
  date: string;
  image: string;
  disease: string;
  confidence: number;
  severity: 'Low' | 'Medium' | 'High';
  cropType: string;
  status: 'Treated' | 'In Progress' | 'Pending';
}

export function History() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  // Mock history data
  const historyData: HistoryItem[] = [
    {
      id: '1',
      date: '2024-01-15',
      image: 'https://images.unsplash.com/photo-1620055494738-248ba57ed714?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwbGFudCUyMGxlYWYlMjBkaXNlYXNlfGVufDF8fHx8MTc1ODg3ODM4NHww&ixlib=rb-4.1.0&q=80&w=1080',
      disease: 'Leaf Spot Disease',
      confidence: 87,
      severity: 'Medium',
      cropType: 'Tomato',
      status: 'Treated'
    },
    {
      id: '2',
      date: '2024-01-14',
      image: 'https://images.unsplash.com/photo-1620055494738-248ba57ed714?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwbGFudCUyMGxlYWYlMjBkaXNlYXNlfGVufDF8fHx8MTc1ODg3ODM4NHww&ixlib=rb-4.1.0&q=80&w=1080',
      disease: 'Powdery Mildew',
      confidence: 92,
      severity: 'High',
      cropType: 'Cucumber',
      status: 'In Progress'
    },
    {
      id: '3',
      date: '2024-01-13',
      image: 'https://images.unsplash.com/photo-1620055494738-248ba57ed714?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxwbGFudCUyMGxlYWYlMjBkaXNlYXNlfGVufDF8fHx8MTc1ODg3ODM4NHww&ixlib=rb-4.1.0&q=80&w=1080',
      disease: 'Healthy Plant',
      confidence: 95,
      severity: 'Low',
      cropType: 'Lettuce',
      status: 'Treated'
    },
    {
      id: '4',
      date: '2024-01-12',
      image: 'https://images.unsplash.com/photo-1620055494738-248ba57ed714?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHhwbGFudCUyMGxlYWYlMjBkaXNlYXNlfGVufDF8fHx8MTc1ODg3ODM4NHww&ixlib=rb-4.1.0&q=80&w=1080',
      disease: 'Bacterial Blight',
      confidence: 84,
      severity: 'High',
      cropType: 'Pepper',
      status: 'Pending'
    },
    {
      id: '5',
      date: '2024-01-11',
      image: 'https://images.unsplash.com/photo-1620055494738-248ba57ed714?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHhwbGFudCUyMGxlYWYlMjBkaXNlYXNlfGVufDF8fHx8MTc1ODg3ODM4NHww&ixlib=rb-4.1.0&q=80&w=1080',
      disease: 'Nutrient Deficiency',
      confidence: 78,
      severity: 'Medium',
      cropType: 'Corn',
      status: 'In Progress'
    }
  ];

  const filteredData = historyData.filter(item => {
    const matchesSearch = item.disease.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         item.cropType.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesSeverity = filterSeverity === 'all' || item.severity.toLowerCase() === filterSeverity;
    const matchesStatus = filterStatus === 'all' || item.status.toLowerCase().replace(' ', '') === filterStatus;
    
    return matchesSearch && matchesSeverity && matchesStatus;
  });

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'Low': return 'bg-green-100 text-green-800';
      case 'Medium': return 'bg-yellow-100 text-yellow-800';
      case 'High': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Treated': return 'bg-green-100 text-green-800';
      case 'In Progress': return 'bg-blue-100 text-blue-800';
      case 'Pending': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl text-gray-900">Analysis History</h1>
          <p className="text-gray-600">View and manage your crop analysis records</p>
        </div>
        <Button className="bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600">
          <Download className="h-4 w-4 mr-2" />
          Export Data
        </Button>
      </div>

      {/* Filters */}
      <Card className="border-green-100">
        <CardContent className="p-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by disease or crop type..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10 border-green-200 focus:border-green-500"
                />
              </div>
            </div>
            <Select value={filterSeverity} onValueChange={setFilterSeverity}>
              <SelectTrigger className="w-full sm:w-40 border-green-200">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severity</SelectItem>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
              </SelectContent>
            </Select>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-full sm:w-40 border-green-200">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="treated">Treated</SelectItem>
                <SelectItem value="inprogress">In Progress</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Results Summary */}
      {filteredData.length > 0 && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Showing {filteredData.length} of {historyData.length} results</span>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            <span>Filters applied</span>
          </div>
        </div>
      )}

      {/* History Grid */}
      {filteredData.length === 0 ? (
        <Card className="border-green-100">
          <CardContent className="p-12 text-center">
            <Calendar className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg text-gray-900 mb-2">No Analysis Found</h3>
            <p className="text-gray-600">
              {searchTerm || filterSeverity !== 'all' || filterStatus !== 'all'
                ? 'Try adjusting your filters to see more results.'
                : 'Start by uploading your first crop image for analysis.'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredData.map((item) => (
            <Card key={item.id} className="border-green-100 hover:shadow-lg transition-shadow">
              <CardHeader className="p-0">
                <div className="relative">
                  <ImageWithFallback
                    src={item.image}
                    alt={`Analysis of ${item.disease}`}
                    className="w-full h-48 object-cover rounded-t-lg"
                  />
                  <div className="absolute top-2 right-2">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="secondary" size="sm" className="bg-white/80 hover:bg-white">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Download className="h-4 w-4 mr-2" />
                          Download Report
                        </DropdownMenuItem>
                        <DropdownMenuItem className="text-red-600">
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-4 space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="text-lg text-gray-900 mb-1">{item.disease}</h3>
                    <p className="text-sm text-gray-600">{item.cropType}</p>
                  </div>
                  <Badge className={getSeverityColor(item.severity)}>
                    {item.severity}
                  </Badge>
                </div>

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Confidence:</span>
                    <span className="text-gray-900">{item.confidence}%</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Date:</span>
                    <span className="text-gray-900">{formatDate(item.date)}</span>
                  </div>
                  <div className="flex justify-between text-sm items-center">
                    <span className="text-gray-600">Status:</span>
                    <Badge variant="secondary" className={getStatusColor(item.status)}>
                      {item.status}
                    </Badge>
                  </div>
                </div>

                <div className="flex gap-2 pt-2">
                  <Button variant="outline" size="sm" className="flex-1 border-green-200 hover:bg-green-50">
                    <Eye className="h-4 w-4 mr-1" />
                    View
                  </Button>
                  <Button variant="outline" size="sm" className="flex-1 border-green-200 hover:bg-green-50">
                    <Download className="h-4 w-4 mr-1" />
                    Export
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}