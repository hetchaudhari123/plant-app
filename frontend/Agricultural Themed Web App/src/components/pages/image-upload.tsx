import { useState, useRef, useEffect } from 'react';
import { Upload, Image as ImageIcon, AlertCircle, CheckCircle, Loader2, X, Brain, TrendingUp, Award, Target, Leaf } from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Label } from '../ui/label';
import { ScrollArea } from '../ui/scroll-area';
import { ImageWithFallback } from '../figma/ImageWithFallback';
import { createPrediction, getAllModels } from '../../services/modelService';
import { FullScreenLoading } from '../ui/loading';
import { toast } from "sonner";


interface Prediction {
  name: string;
  confidence: number;
}

interface PredictionItem {
  crop: string;
  disease: string;
  confidence: number; // float between 0 and 1
  label: string;
  class_idx: number;
}

interface AnalysisResult {
  prediction_id: string;
  model_name: string;
  user_id: string;
  image_url: string;
  status: string;
  crop: string;
  disease: string;
  raw_output: {
    top_predictions: PredictionItem[];
    primary_confidence: number;
    model: string;
    all_probabilities: number[];
  };
  processing_time: number;
  created_at: string;
  expires_at: string;
  _id?: string;
}
export function ImageUpload() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedModel, setSelectedModel] = useState<Model | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Define the Model type
  interface Model {
    id: string;
    name: string;
    description: string;
    accuracy: number; // Add this field
    alias: string; // Add this field
  }
  // Inside your component:
  const [models, setModels] = useState<Model[]>([]); // Add type annotation
  const formatConfidence = (confidence: number): string => {
    const percentage = confidence * 100;
    if (percentage < 0.01) {
      return '< 0.01%';
    }
    return percentage.toFixed(2) + '%';
  };
  useEffect(() => {
    const fetchModels = async () => {
      setLoading(true); // Set loading at the very start
      setError(null); // Clear any previous errors

      try {
        const response = await getAllModels();

        // Add console logs to debug the ID issue

        // Extract name, description, and id from response
        const formattedModels = response.models.map((model: any) => ({
          id: model.model_id,
          name: model.name,
          description: model.description,
          accuracy: model.accuracy,
          alias: model.alias, // Extract alias from API response
        }));

        console.log('Formatted models:', formattedModels);
        setModels(formattedModels);
      } catch (err: any) {
        console.error('Failed to fetch models:', err);
        setError(err.message || 'Failed to load models');
        setModels([]); // Clear models on error
      } finally {
        setLoading(false); // Always set loading to false
      }
    };

    fetchModels();
  }, []); // Empty dependency array means this runs once on mount

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      setAnalysisResult(null);
    }
  };

  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setSelectedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      setAnalysisResult(null);
    }
  };

  const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
  };

  const analyzeImage = async () => {
    if (!selectedFile) {
      toast.error('Please select an image first');
      return;
    }

    if (!selectedModel) {
      toast.error('Please select a detection model');
      return;
    }

    setIsAnalyzing(true);

    try {
      // Call the prediction API with model alias and file
      const response = await createPrediction(selectedModel.alias, selectedFile);

      setAnalysisResult(response);
      toast.success('Image analyzed successfully!');

      // Optional: Log the results
      console.log('Analysis Result:', response);

    } catch (error: any) {
      console.error('Analysis failed:', error);

      // Better error message extraction
      const errorMessage =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        'Failed to analyze image. Please try again.';

      toast.error(errorMessage);
      setAnalysisResult(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const clearImage = () => {
    setSelectedFile(null);
    setPreviewUrl('');
    setAnalysisResult(null);
    setUploadProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'bg-green-600 text-white';
    if (confidence >= 70) return 'bg-green-500 text-white';
    if (confidence >= 50) return 'bg-yellow-500 text-white';
    if (confidence >= 30) return 'bg-orange-500 text-white';
    return 'bg-red-500 text-white';
  };

  const getConfidenceBarColor = (confidence: number) => {
    if (confidence >= 90) return 'bg-green-600';
    if (confidence >= 70) return 'bg-green-500';
    if (confidence >= 50) return 'bg-yellow-500';
    if (confidence >= 30) return 'bg-orange-500';
    return 'bg-red-500';
  };
  // Add this helper function at the top of your component
  const toTitleCase = (text: string): string => {
    return text
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(' ');
  };
  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-gray-900">Plant Disease Detection</h1>
        <p className="text-muted-foreground">
          Upload an image of a plant leaf and select a model to detect diseases
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Upload and Model Selection Section */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-green-100 shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Upload Plant Image
              </CardTitle>
              <CardDescription>
                Upload a clear image of the plant leaf
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!selectedFile ? (
                <div
                  className="border-2 border-dashed border-green-300 rounded-xl p-8 text-center hover:border-green-400 transition-colors cursor-pointer"
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <div className="space-y-4">
                    <div className="flex justify-center">
                      <div className="bg-green-100 p-3 rounded-full">
                        <ImageIcon className="h-8 w-8 text-green-600" />
                      </div>
                    </div>
                    <div>
                      <p className="text-gray-900 mb-2">
                        Drop your image here
                      </p>
                      <p className="text-sm text-gray-500">
                        or click to browse
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="relative">
                    <ImageWithFallback
                      src={previewUrl}
                      alt="Selected plant image"
                      className="w-full h-48 object-cover rounded-xl border border-green-200"
                    />
                    <button
                      onClick={clearImage}
                      className="absolute top-2 right-2 bg-red-500 hover:bg-red-600 text-white p-1.5 rounded-full shadow-md transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="text-sm text-muted-foreground bg-green-50 p-3 rounded-lg">
                    <p className="truncate"><strong>File:</strong> {selectedFile.name}</p>
                    <p><strong>Size:</strong> {(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
              )}

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileSelect}
                className="hidden"
              />

              <div className="flex gap-2">
                <Button
                  onClick={() => fileInputRef.current?.click()}
                  variant="outline"
                  className="flex-1 border-green-200 hover:bg-green-50 rounded-xl"
                >
                  <ImageIcon className="h-4 w-4 mr-2" />
                  Browse
                </Button>

              </div>
            </CardContent>
          </Card>

          {/* Model Selection */}

          <Card className="border-green-100 shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Select Detection Model
              </CardTitle>
              <CardDescription>
                Choose a model for disease detection
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RadioGroup value={selectedModel?.id || ''} onValueChange={(value) => {
                const model = models.find(m => m.id === value);
                setSelectedModel(model || null);
              }}>
                <div className="space-y-3">
                  {models.map((model) => (
                    <div
                      key={model.id}
                      className={`flex items-start gap-3 p-3 rounded-lg transition-all cursor-pointer border-2 ${selectedModel?.id === model.id
                        ? 'bg-green-50 border-green-500 shadow-md'
                        : 'border-transparent hover:bg-green-50 hover:border-green-200'
                        }`}
                      onClick={() => setSelectedModel(model)}
                    >
                      {/* Custom icon instead of RadioGroupItem */}
                      <div className="mt-1 shrink-0">
                        {selectedModel?.id === model.id ? (
                          <div className="w-5 h-5 rounded-full bg-green-600 flex items-center justify-center">
                            <Leaf className="h-3 w-3 text-white" />
                          </div>
                        ) : (
                          <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
                        )}
                      </div>

                      <div className="flex-1 flex items-start gap-4">
                        <div className="flex-1 min-w-0">
                          <p className={`font-medium ${selectedModel?.id === model.id ? 'text-green-700' : 'text-foreground'}`}>
                            {model.name}
                          </p>
                          <p className="text-xs text-muted-foreground mt-0.5 break-words">
                            {model.description}
                          </p>
                        </div>
                        <div className="flex flex-col items-end gap-1 shrink-0 ml-auto">
                          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md whitespace-nowrap ${selectedModel?.id === model.id
                            ? 'bg-green-600 text-white'
                            : 'bg-green-100 text-green-700'
                            }`}>
                            <Target className="h-3.5 w-3.5" />
                            <span className="text-sm font-semibold">
                              {(model.accuracy * 100).toFixed(1)}%
                            </span>
                          </div>
                          <span className="text-xs text-muted-foreground whitespace-nowrap">Accuracy</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </RadioGroup>
            </CardContent>
          </Card>

          {/* Analyze Button */}
          {selectedFile && (
            <Button
              onClick={analyzeImage}
              disabled={isAnalyzing}
              className="w-full bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 rounded-xl shadow-md"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Analyzing Image...
                </>
              ) : (
                <>
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Analyze Image
                </>
              )}
            </Button>
          )}

          {isAnalyzing && (
            <Card className="border-green-100 shadow-md">
              <CardContent className="pt-6">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm text-muted-foreground">
                    <span>Processing...</span>
                    <span>{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} className="h-2" />
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Results Section */}
        <div className="lg:col-span-3">
          <Card className="border-green-100 shadow-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Prediction Results
              </CardTitle>
              <CardDescription>
                Disease detection results from the selected model
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!analysisResult ? (
                <div className="text-center py-16 text-muted-foreground">
                  <ImageIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
                  <p>Upload an image and click analyze to see results</p>
                  <p className="text-sm mt-2">Select a model and submit to get predictions</p>
                </div>
              ) : (
                <div className="space-y-6">
                  {/* Model Used Info */}
                  <div className="flex items-center gap-2 text-sm text-muted-foreground bg-blue-50 p-3 rounded-lg">
                    <Brain className="h-4 w-4 text-blue-600" />
                    <span>Model Used: <strong className="text-blue-700">{analysisResult.model_name}</strong></span>
                  </div>

                  {/* Primary Crop and Disease */}
                  <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-xl border-2 border-green-200">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="bg-green-600 p-2 rounded-lg">
                          <Award className="h-6 w-6 text-white" />
                        </div>
                        <div>
                          <p className="text-sm text-green-700 uppercase tracking-wide">Detected Disease</p>
                          <h3 className="text-2xl font-bold text-gray-900 mt-1">
                            {toTitleCase(analysisResult.disease || 'Unknown')}
                          </h3>
                          <p className="text-sm text-green-600 mt-1">
                            Crop: {toTitleCase(analysisResult.crop || 'Unknown')}
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="flex-1 bg-white/50 rounded-full h-3 overflow-hidden">
                        <div
                          className="h-full bg-green-600 transition-all duration-500"
                          style={{
                            width: `${(analysisResult.raw_output?.primary_confidence || 0) * 100}%`
                          }}
                        />
                      </div>
                      <Badge className="bg-green-600 text-white px-3 py-1">
                        {((analysisResult.raw_output?.primary_confidence || 0) * 100).toFixed(2)}%
                      </Badge>
                    </div>
                  </div>

                  {/* All Predictions List */}
                  {analysisResult.raw_output?.top_predictions && (
                    <div>
                      <h4 className="text-gray-900 mb-4 flex items-center gap-2">
                        <CheckCircle className="h-5 w-5 text-green-600" />
                        Top {analysisResult.raw_output.top_predictions.length} Predictions
                      </h4>
                      <ScrollArea className="h-[380px] pr-4">
                        <div className="space-y-3">
                          {analysisResult.raw_output.top_predictions.map((prediction: any, index: number) => (
                            <Card key={index} className="border border-gray-200 hover:border-green-300 transition-colors">
                              <CardContent className="p-4">
                                <div className="flex items-center justify-between mb-3">
                                  <div className="flex items-center gap-3">
                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${index === 0 ? 'bg-green-600' : 'bg-gray-200'
                                      }`}>
                                      <span className={`font-semibold ${index === 0 ? 'text-white' : 'text-gray-600'
                                        }`}>
                                        {index + 1}
                                      </span>
                                    </div>
                                    <div>
                                      <p className="font-semibold text-gray-900">{toTitleCase(prediction.disease)}</p>
                                      <p className="text-sm text-muted-foreground">
                                        Crop: {toTitleCase(prediction.crop)}
                                      </p>
                                    </div>
                                  </div>
                                  <Badge className={getConfidenceColor(prediction.confidence * 100)}>
                                    {formatConfidence(prediction.confidence)}
                                  </Badge>
                                </div>
                                <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                                  <div
                                    className={`h-full transition-all duration-500 ${getConfidenceBarColor(prediction.confidence * 100)
                                      }`}
                                    style={{ width: `${prediction.confidence * 100}%` }}
                                  />
                                </div>
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>
                  )}

                  {/* Action Buttons */}
                  {/* <div className="flex gap-3 pt-4 border-t">
                    <Button
                      variant="outline"
                      className="flex-1 rounded-xl border-green-200 hover:bg-green-50"
                      onClick={clearImage}
                    >
                      Analyze Another
                    </Button>
                    <Button className="flex-1 bg-gradient-to-r from-green-600 to-green-500 hover:from-green-700 hover:to-green-600 rounded-xl">
                      Save Results
                    </Button>
                  </div> */}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Quick Tips */}
      <Card className="border-green-100 bg-green-50 shadow-md">
        <CardContent className="p-6">
          <h3 className="text-green-800 mb-4">Tips for Better Detection</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-green-700">
            <div className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
              <span>Take photos in good natural lighting</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
              <span>Focus on affected areas of the leaf</span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
              <span>Ensure the leaf fills most of the frame</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}