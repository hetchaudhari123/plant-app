import { useEffect, useState } from 'react';
import { Calendar, Download, Filter, Search, Eye, Trash2, MoreVertical, Loader2 } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../ui/dropdown-menu';
import { ImageWithFallback } from '../figma/ImageWithFallback';
import { deletePrediction, getUserPredictions } from '../../services/modelService';
import { toast } from 'sonner';
// Type definitions
interface Prediction {
  prediction_id: string;
  created_at: string;
  date?: string;
  image_url: string;
  disease: string;
  confidence?: number;
  crop: string;
  model_name?: string;
  raw_output?: {
    primary_confidence?: number;
    [key: string]: any;
  };
}

interface PredictionsResponse {
  predictions: Prediction[];
  total: number;
  skip: number;
  limit: number;
}

interface HistoryItem {
  id: string;
  date: string;
  image: string;
  disease: string;
  confidence: number;
  cropType: string;
  status: string;
}

export function History() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [historyData, setHistoryData] = useState<HistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const toTitleCase = (text: string): string => {
    return text
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };
  // Extract the fetch function outside useEffect
  const fetchPredictions = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getUserPredictions({
        skip: 0,
        limit: 100,
        sort_by: "created_at",
        sort_order: -1
      });

      console.log('API Response:', response);

      if (!response) {
        throw new Error('No response received from server');
      }

      if (!response.predictions || !Array.isArray(response.predictions)) {
        throw new Error('Invalid response format: predictions array not found');
      }

      // Transform predictions to HistoryItem format
      const transformedData: HistoryItem[] = response.predictions.map((pred: any) => ({
        id: pred.prediction_id,
        date: pred.created_at || pred.date,
        image: pred.image_url,
        disease: pred.disease,
        confidence: Math.round((pred.raw_output?.primary_confidence ?? pred.confidence ?? 0) * 100),
        cropType: pred.crop,
        status: 'Completed'
      }));

      setHistoryData(transformedData);
    } catch (err: any) {
      console.error('Error fetching predictions:', err);
      setError(err.message || 'Failed to fetch predictions');
    } finally {
      setLoading(false);
    }
  };

  // Call on mount
  useEffect(() => {
    fetchPredictions();
  }, []);

  const filteredData = historyData.filter(item => {
    const matchesSearch = item.disease.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.cropType.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || item.status.toLowerCase().replace(' ', '') === filterStatus;

    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Treated': return 'bg-green-100 text-green-800';
      case 'In Progress': return 'bg-blue-100 text-blue-800';
      case 'Pending': return 'bg-gray-100 text-gray-800';
      case 'Completed': return 'bg-green-100 text-green-800';
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

  const handleDelete = async (predictionId: string) => {
    try {
      // Optimistically remove from UI immediately
      setHistoryData(prev => prev.filter(item => item.id !== predictionId));

      // Then delete from backend
      await deletePrediction(predictionId);
      toast.success("Prediction deleted successfully");
    } catch (error) {
      console.error("Failed to delete prediction:", error);
      toast.error("Failed to delete prediction. Please try again.");

      // Refetch on error to restore correct state
      await fetchPredictions();
    }
  };

  // Loading state
  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <div className="flex flex-col items-center justify-center min-h-[400px]">
          <Loader2 className="h-12 w-12 text-green-600 animate-spin mb-4" />
          <h3 className="text-lg text-gray-900 mb-2">Loading Analysis History</h3>
          <p className="text-gray-600">Please wait while we fetch your records...</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="max-w-7xl mx-auto p-6">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-12 text-center">
            <div className="text-red-600 mb-4">
              <Calendar className="h-16 w-16 mx-auto mb-4" />
            </div>
            <h3 className="text-lg text-gray-900 mb-2">Error Loading History</h3>
            <p className="text-gray-600 mb-4">{error}</p>
            <Button
              onClick={() => window.location.reload()}
              className="bg-green-600 hover:bg-green-700"
            >
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-gray-900">Analysis History</h1>
          <p className="text-gray-600">View and manage your crop analysis records</p>
        </div>
        {/* <Button className="bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600">
          <Download className="h-4 w-4 mr-2" />
          Export Data
        </Button> */}
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
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-full sm:w-40 border-green-200">
                <SelectValue placeholder="Status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="treated">Treated</SelectItem>
                <SelectItem value="inprogress">In Progress</SelectItem>
                <SelectItem value="pending">Pending</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Results Summary */}
      {/* {filteredData.length > 0 && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>Showing {filteredData.length} of {historyData.length} results</span>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            <span>Filters applied</span>
          </div>
        </div>
      )} */}

      {/* History Grid */}
      {filteredData.length === 0 ? (
        <Card className="border-green-100">
          <CardContent className="p-12 text-center">
            <Calendar className="h-16 w-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg text-gray-900 mb-2">No Analysis Found</h3>
            <p className="text-gray-600">
              {searchTerm || filterStatus !== 'all'
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
                    alt={`Analysis of ${toTitleCase(item.disease)}`}
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
                        {/* <DropdownMenuItem>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem>
                          <Download className="h-4 w-4 mr-2" />
                          Download Report
                        </DropdownMenuItem> */}
                        <DropdownMenuItem
                          className="text-red-600"
                          onClick={(e) => {
                            e.preventDefault();
                            // Show confirmation dialog
                            // if (window.confirm("Are you sure you want to delete this prediction?")) {
                            handleDelete(item.id);
                            // }
                          }}
                        >
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-4 space-y-3">
                <div className="text-center">
                  <h3 className="text-lg text-gray-900 mb-1">{toTitleCase(item.disease)}</h3>
                  <p className="text-sm text-gray-600">{toTitleCase(item.cropType)}</p>
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

                {/* <div className="flex gap-2 pt-2">
                  <Button variant="outline" size="sm" className="flex-1 border-green-200 hover:bg-green-50">
                    <Eye className="h-4 w-4 mr-1" />
                    View
                  </Button>
                  <Button variant="outline" size="sm" className="flex-1 border-green-200 hover:bg-green-50">
                    <Download className="h-4 w-4 mr-1" />
                    Export
                  </Button>
                </div> */}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}