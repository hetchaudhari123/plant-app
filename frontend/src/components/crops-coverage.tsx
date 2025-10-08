import { useState } from 'react';
import { Search, Filter, Leaf } from 'lucide-react';
import { Input } from './ui/input';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from './ui/select';

interface Disease {
    name: string;
    severity: 'low' | 'medium' | 'high';
}

interface Crop {
    id: string;
    name: string;
    icon: string;
    diseases: Disease[];
    category: string;
}

const cropsData: Crop[] = [
    {
        id: 'pearl-millet',
        name: 'Pearl Millet',
        icon: '🌾',
        category: 'Cereals',
        diseases: [
            { name: 'Rust', severity: 'high' },
            { name: 'Downy Mildew', severity: 'high' },
            { name: 'Blast', severity: 'high' },
            { name: 'Brown Spot', severity: 'medium' },
            { name: 'Healthy', severity: 'low' }
        ]
    },
    {
        id: 'apple',
        name: 'Apple',
        icon: '🍎',
        category: 'Fruits',
        diseases: [
            { name: 'Apple Scab', severity: 'high' },
            { name: 'Black Rot', severity: 'high' },
            { name: 'Cedar Apple Rust', severity: 'medium' },
            { name: 'Healthy', severity: 'low' }
        ]
    },
    {
        id: 'bell-pepper',
        name: 'Bell Pepper',
        icon: '🫑',
        category: 'Vegetables',
        diseases: [
            { name: 'Bacterial Spot', severity: 'high' },
            { name: 'Healthy', severity: 'low' }
        ]
    },
    {
        id: 'tomato',
        name: 'Tomato',
        icon: '🍅',
        category: 'Vegetables',
        diseases: [
            { name: 'Yellow Leaf Curl Virus', severity: 'high' },
            { name: 'Early Blight', severity: 'high' },
            { name: 'Late Blight', severity: 'high' },
            { name: 'Septoria Leaf Spot', severity: 'medium' },
            { name: 'Bacterial Spot', severity: 'medium' },
            { name: 'Healthy', severity: 'low' }
        ]
    },
    {
        id: 'potato',
        name: 'Potato',
        icon: '🥔',
        category: 'Vegetables',
        diseases: [
            { name: 'Early Blight', severity: 'high' },
            { name: 'Late Blight', severity: 'high' },
            { name: 'Healthy', severity: 'low' }
        ]
    },
    {
        id: 'grape',
        name: 'Grape',
        icon: '🍇',
        category: 'Fruits',
        diseases: [
            { name: 'Esca (Black Measles)', severity: 'high' },
            { name: 'Black Rot', severity: 'high' },
            { name: 'Leaf Blight', severity: 'medium' },
            { name: 'Healthy', severity: 'low' }
        ]
    },
    {
        id: 'corn',
        name: 'Corn',
        icon: '🌽',
        category: 'Cereals',
        diseases: [
            { name: 'Northern Leaf Blight', severity: 'high' },
            { name: 'Common Rust', severity: 'high' },
            { name: 'Cercospora Leaf Spot', severity: 'medium' },
            { name: 'Healthy', severity: 'low' }
        ]
    },
    {
        id: 'peach',
        name: 'Peach',
        icon: '🍑',
        category: 'Fruits',
        diseases: [
            { name: 'Bacterial Spot', severity: 'high' },
            { name: 'Healthy', severity: 'low' }
        ]
    },
    {
        id: 'cherry',
        name: 'Cherry',
        icon: '🍒',
        category: 'Fruits',
        diseases: [
            { name: 'Powdery Mildew', severity: 'medium' },
            { name: 'Healthy', severity: 'low' }
        ]
    },
    {
        id: 'strawberry',
        name: 'Strawberry',
        icon: '🍓',
        category: 'Fruits',
        diseases: [
            { name: 'Leaf Scorch', severity: 'medium' },
            { name: 'Healthy', severity: 'low' }
        ]
    },
    {
        id: 'rice',
        name: 'Rice',
        icon: '🌾',
        category: 'Cereals',
        diseases: [
            { name: 'Blast', severity: 'high' },
            { name: 'Tungro', severity: 'high' },
            { name: 'Leaf Smut', severity: 'low' }
        ]
    },
    {
        id: 'cotton',
        name: 'Cotton',
        icon: '🌱',
        category: 'Cash Crops',
        diseases: [
            { name: 'Bacterial Blight', severity: 'medium' },
            { name: 'Wilt', severity: 'medium' },
            { name: 'Leaf Curl', severity: 'medium' },
            { name: 'Aphid', severity: 'low' },
            { name: 'Mealy Bug', severity: 'low' },
            { name: 'American Bollworm', severity: 'low' },
            { name: 'Red Cotton Bug', severity: 'low' },
            { name: 'Whitefly', severity: 'low' },
            { name: 'Thirps', severity: 'low' },
            { name: 'Pink Bollworm', severity: 'low' },
            { name: 'Anthracnose', severity: 'low' },
            { name: 'Healthy', severity: 'low' }
        ]
    },
    {
        id: 'sugarcane',
        name: 'Sugarcane',
        icon: '🎋',
        category: 'Cash Crops',
        diseases: [
            { name: 'Red Rot', severity: 'medium' },
            { name: 'Yellow Rust', severity: 'medium' },
            { name: 'Mosaic', severity: 'medium' },
            { name: 'Red Rust', severity: 'low' },
            { name: 'Healthy', severity: 'low' }
        ]
    }
];

const getSeverityColor = (severity: string) => {
    switch (severity) {
        case 'high':
            return 'bg-red-100 text-red-800 border-red-200';
        case 'medium':
            return 'bg-yellow-100 text-yellow-800 border-yellow-200';
        case 'low':
            return 'bg-green-100 text-green-800 border-green-200';
        default:
            return 'bg-gray-100 text-gray-800 border-gray-200';
    }
};

export function CropsCoverage() {
    const [selectedCategory, setSelectedCategory] = useState('all');
    const [searchTerm, setSearchTerm] = useState('');

    // Get unique categories
    const categories = ['all', ...Array.from(new Set(cropsData.map((crop) => crop.category)))];

    // Filter crops based on search and category
    const filteredCrops = cropsData.filter((crop) => {
        const matchesSearch =
            crop.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            crop.diseases.some((disease) =>
                disease.name.toLowerCase().includes(searchTerm.toLowerCase())
            );
        const matchesCategory = selectedCategory === 'all' || crop.category === selectedCategory;
        return matchesSearch && matchesCategory;
    });

    return (
        <div className="min-h-screen bg-gradient-to-b from-green-50 to-white py-12 px-4 sm:px-6 lg:px-8">
            <div className="max-w-7xl mx-auto">
                {/* Header Section */}
                <div className="text-center mb-8">
                    <div className="flex items-center justify-center mb-6">
                        <div className="bg-green-100 p-4 rounded-full w-20 h-20 flex items-center justify-center flex-shrink-0">
                            <Leaf className="h-10 w-10 text-green-600" />
                        </div>
                    </div>
                    <h1 className="text-gray-900 mb-4 text-4xl font-bold">Supported Crops & Diseases</h1>
                    <p className="text-gray-600 max-w-2xl mx-auto text-lg">
                        Explore the crops and plant diseases that our app can currently predict.
                    </p>
                    <div className="mt-4 flex items-center justify-center gap-6 text-sm text-gray-500">
                        <div className="flex items-center gap-3">
                            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                            <span>{cropsData.length} Crops Supported</span>
                        </div>
                        <div className="flex items-center gap-3">
                            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                            <span>
                                {cropsData.reduce((acc, crop) => acc + crop.diseases.length, 0)} Diseases Detected
                            </span>
                        </div>
                    </div>
                </div>

                {/* Search and Filter Section */}
                <div className="mb-6 bg-white p-6 rounded-lg shadow-sm border border-green-100">
                    <div className="flex flex-col md:flex-row gap-4">
                        {/* Search Bar */}

                        <div className="relative flex-1">
                            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                            <Input
                                placeholder="Search by disease or crop type..."
                                value={searchTerm}
                                onChange={(e) => {
                                    setSearchTerm(e.target.value)
                                }}
                                className="pl-10 border-green-200 focus:border-green-500"
                            />
                        </div>

                        {/* Category Filter */}
                        <div className="md:w-64">
                            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                                <SelectTrigger className="border-green-200">
                                    <Filter className="h-4 w-4 mr-2 text-gray-500" />
                                    <SelectValue placeholder="Filter by category" />
                                </SelectTrigger>
                                <SelectContent>
                                    {categories.map((category) => (
                                        <SelectItem key={category} value={category}>
                                            {category === 'all' ? 'All Categories' : category}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    </div>

                    {/* Active Filters Display */}
                    {(searchTerm || selectedCategory !== 'all') && (
                        <div className="mt-4 flex items-center gap-2 flex-wrap">
                            <span className="text-sm text-gray-600">Active filters:</span>
                            {searchTerm && (
                                <Badge variant="secondary" className="bg-green-100 text-green-800">
                                    Search: "{searchTerm}"
                                    <button
                                        onClick={() => setSearchTerm('')}
                                        className="ml-2 hover:text-green-900"
                                    >
                                        ×
                                    </button>
                                </Badge>
                            )}
                            {selectedCategory !== 'all' && (
                                <Badge variant="secondary" className="bg-green-100 text-green-800">
                                    Category: {selectedCategory}
                                    <button
                                        onClick={() => setSelectedCategory('all')}
                                        className="ml-2 hover:text-green-900"
                                    >
                                        ×
                                    </button>
                                </Badge>
                            )}
                        </div>
                    )}
                </div>

                {/* Results Count */}
                <div className="mb-6">
                    <p className="text-sm text-gray-600">
                        Showing <span className="text-green-700">{filteredCrops.length}</span> of{' '}
                        <span className="text-green-700">{cropsData.length}</span> crops
                    </p>
                </div>

                {/* Crops Grid */}
                {filteredCrops.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {filteredCrops.map((crop) => (
                            <Card
                                key={crop.id}
                                className="border-green-100 hover:shadow-lg transition-shadow duration-300 hover:border-green-300"
                            >
                                <CardHeader className="pb-4">
                                    <div className="flex items-center gap-4">
                                        <div className="text-4xl">{crop.icon}</div>
                                        <div className="flex-1">
                                            <CardTitle className="text-xl text-gray-900 mb-1">{crop.name}</CardTitle>
                                            <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                                                {crop.category}
                                            </Badge>
                                        </div>
                                    </div>
                                </CardHeader>
                                <CardContent>
                                    <div className="space-y-3">
                                        <div className="flex items-center justify-between">
                                            <span className="text-sm text-gray-600">Detectable Diseases:</span>
                                            <Badge className="bg-green-600 text-white">{crop.diseases.length}</Badge>
                                        </div>
                                        <div className="flex flex-wrap gap-2">
                                            {crop.diseases.map((disease, index) => (
                                                <Badge
                                                    key={index}
                                                    variant="outline"
                                                    className={`text-xs ${getSeverityColor(disease.severity)}`}
                                                >
                                                    {disease.name}
                                                </Badge>
                                            ))}
                                        </div>
                                    </div>
                                </CardContent>
                            </Card>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-12">
                        <div className="bg-gray-100 rounded-full w-20 h-20 flex items-center justify-center mx-auto mb-4">
                            <Search className="h-10 w-10 text-gray-400" />
                        </div>
                        <h3 className="text-gray-900 mb-2">No crops found</h3>
                        <p className="text-gray-600 mb-4">
                            Try adjusting your search or filter criteria
                        </p>
                        <Button
                            variant="outline"
                            onClick={() => {
                                setSearchTerm('');
                                setSelectedCategory('all');
                            }}
                            className="border-green-200 hover:bg-green-50"
                        >
                            Clear All Filters
                        </Button>
                    </div>
                )}

                {/* Info Section */}
                <div className="mt-6 bg-gradient-to-r from-green-50 to-green-100 p-8 rounded-lg border border-green-200">
                    <div className="grid md:grid-cols-3 gap-6 text-center">
                        <div>
                            <div className="text-3xl text-green-600 mb-2">
                                {cropsData.length}+
                            </div>
                            <p className="text-sm text-gray-700">Crop Types</p>
                        </div>
                        <div>
                            <div className="text-3xl text-green-600 mb-2">
                                {cropsData.reduce((acc, crop) => acc + crop.diseases.length, 0)}+
                            </div>
                            <p className="text-sm text-gray-700">Disease Predictions</p>
                        </div>
                        <div>
                            <div className="text-3xl text-green-600 mb-2">99%</div>
                            <p className="text-sm text-gray-700">Accuracy Rate</p>
                        </div>
                    </div>
                    <div className="mt-6 text-center">
                        <p className="text-sm text-gray-600">
                            Our AI model is continuously learning and expanding. More crops and diseases will be added soon!
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
