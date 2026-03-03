import { useState, useRef } from 'react';
import { useParams } from 'react-router';
import DoctorLayout from '@/components/layout/FIGMA/DoctorLayout';
import { 
  Upload, 
  Brain, 
  ZoomIn, 
  ZoomOut, 
  Maximize2,
  Download,
  AlertCircle,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  FileImage,
  X,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { Card } from '@/components/ui/FIGMA/card';
import { Button } from '@/components/ui/FIGMA/button';
import { Badge } from '@/components/ui/FIGMA/badge';
import { Progress } from '@/components/ui/FIGMA/progress';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/FIGMA/avatar';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { ImageWithFallback } from '@/components/layout/FIGMA/figma/ImageWithFallback';

interface AnalysisResult {
  confidence: number;
  findings: {
    type: 'normal' | 'attention' | 'critical';
    text: string;
    severity: string;
  }[];
  recommendations: string[];
}

const mockPatient = {
  id: '1',
  name: 'Ahmed Hassan',
  age: 45,
  gender: 'Male',
  bloodType: 'A+',
  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ahmed',
  medicalHistory: [
    { date: '2024-01-15', event: 'Regular checkup', type: 'success' },
    { date: '2024-02-01', event: 'MRI scan requested', type: 'info' },
    { date: '2024-02-05', event: 'Follow-up scheduled', type: 'warning' },
  ],
  allergies: ['Penicillin', 'Latex'],
  medications: ['Aspirin 100mg', 'Lisinopril 10mg'],
  vitals: {
    heartRate: 72,
    bloodPressure: '120/80',
    temperature: 37.2,
  },
};

const previousScans = [
  { id: 1, date: '2024-01-20', url: 'https://images.unsplash.com/photo-1758691463165-ca9b5bc2b28a?w=400' },
  { id: 2, date: '2023-12-15', url: 'https://images.unsplash.com/photo-1758691463165-ca9b5bc2b28a?w=400' },
  { id: 3, date: '2023-11-10', url: 'https://images.unsplash.com/photo-1758691463165-ca9b5bc2b28a?w=400' },
];

export default function MRIAnalysis() {
  const { patientId } = useParams();
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [zoom, setZoom] = useState(100);
  const [currentScanIndex, setCurrentScanIndex] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage(e.target?.result as string);
        toast.success('MRI scan uploaded successfully');
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDrop = (event: React.DragEvent) => {
    event.preventDefault();
    const file = event.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage(e.target?.result as string);
        toast.success('MRI scan uploaded successfully');
      };
      reader.readAsDataURL(file);
    } else {
      toast.error('Please upload a valid image file');
    }
  };

  const handleDragOver = (event: React.DragEvent) => {
    event.preventDefault();
  };

  const analyzeImage = async () => {
    if (!selectedImage) {
      toast.error('Please upload an MRI scan first');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisProgress(0);

    // Simulate AI analysis
    const interval = setInterval(() => {
      setAnalysisProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 5;
      });
    }, 100);

    setTimeout(() => {
      setIsAnalyzing(false);
      setAnalysisResult({
        confidence: 94.5,
        findings: [
          { type: 'normal', text: 'No signs of hemorrhage detected', severity: 'Normal' },
          { type: 'normal', text: 'Brain structure appears normal', severity: 'Normal' },
          { type: 'attention', text: 'Minor white matter changes noted', severity: 'Low' },
          { type: 'attention', text: 'Slight ventricular enlargement', severity: 'Medium' },
        ],
        recommendations: [
          'Continue monitoring white matter changes',
          'Schedule follow-up MRI in 6 months',
          'Consider lifestyle modifications for vascular health',
          'Review patient history for risk factors',
        ],
      });
      toast.success('Analysis completed successfully');
    }, 2000);
  };

  const loadPreviousScan = (url: string) => {
    setSelectedImage(url);
    setAnalysisResult(null);
    toast.info('Previous scan loaded');
  };

  return (
    <DoctorLayout>
      <div className="p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <h1 className="text-3xl font-bold mb-2">MRI Analysis</h1>
          <p className="text-gray-600 dark:text-gray-400">
            AI-powered brain scan analysis and diagnosis
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Patient Info Panel */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            {/* Patient Card */}
            <Card className="p-6">
              <div className="flex items-center gap-4 mb-6">
                <Avatar className="w-16 h-16">
                  <AvatarImage src={mockPatient.avatar} />
                  <AvatarFallback>{mockPatient.name[0]}</AvatarFallback>
                </Avatar>
                <div>
                  <h2 className="text-xl font-bold">{mockPatient.name}</h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {mockPatient.age} years • {mockPatient.gender}
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Blood Type</p>
                  <Badge variant="outline" className="font-semibold">{mockPatient.bloodType}</Badge>
                </div>

                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Allergies</p>
                  <div className="flex flex-wrap gap-2">
                    {mockPatient.allergies.map((allergy) => (
                      <Badge key={allergy} variant="destructive" className="text-xs">
                        {allergy}
                      </Badge>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Current Medications</p>
                  <div className="space-y-1">
                    {mockPatient.medications.map((med) => (
                      <p key={med} className="text-sm px-3 py-2 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                        💊 {med}
                      </p>
                    ))}
                  </div>
                </div>

                <div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Vital Signs</p>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-red-50 dark:bg-red-950/20 rounded-lg">
                      <p className="text-xs text-gray-600 dark:text-gray-400">Heart Rate</p>
                      <p className="text-lg font-bold text-red-600">{mockPatient.vitals.heartRate} bpm</p>
                    </div>
                    <div className="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                      <p className="text-xs text-gray-600 dark:text-gray-400">BP</p>
                      <p className="text-lg font-bold text-blue-600">{mockPatient.vitals.bloodPressure}</p>
                    </div>
                    <div className="p-3 bg-orange-50 dark:bg-orange-950/20 rounded-lg col-span-2">
                      <p className="text-xs text-gray-600 dark:text-gray-400">Temperature</p>
                      <p className="text-lg font-bold text-orange-600">{mockPatient.vitals.temperature}°C</p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>

            {/* Medical History */}
            <Card className="p-6">
              <h3 className="font-bold mb-4">Medical History</h3>
              <div className="space-y-3">
                {mockPatient.medicalHistory.map((item, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3 + index * 0.1 }}
                    className="flex gap-3 items-start"
                  >
                    <div className={`w-2 h-2 rounded-full mt-2 ${
                      item.type === 'success' ? 'bg-green-500' :
                      item.type === 'warning' ? 'bg-yellow-500' :
                      'bg-blue-500'
                    }`} />
                    <div className="flex-1">
                      <p className="text-sm font-medium">{item.event}</p>
                      <p className="text-xs text-gray-500">{item.date}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </Card>

            {/* Previous Scans */}
            <Card className="p-6">
              <h3 className="font-bold mb-4">Previous Scans</h3>
              <div className="grid grid-cols-3 gap-3">
                {previousScans.map((scan) => (
                  <motion.div
                    key={scan.id}
                    whileHover={{ scale: 1.05 }}
                    className="cursor-pointer"
                    onClick={() => loadPreviousScan(scan.url)}
                  >
                    <div className="aspect-square rounded-lg overflow-hidden border-2 border-gray-200 dark:border-gray-700 hover:border-blue-500 transition-colors">
                      <ImageWithFallback
                        src={scan.url}
                        alt={`Scan ${scan.date}`}
                        className="w-full h-full object-cover"
                      />
                    </div>
                    <p className="text-xs text-center mt-1 text-gray-600">{scan.date}</p>
                  </motion.div>
                ))}
              </div>
            </Card>
          </motion.div>

          {/* Analysis Panel */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-2 space-y-6"
          >
            {/* Upload/View Area */}
            <Card className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-bold">MRI Scan Viewer</h2>
                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setZoom(Math.max(50, zoom - 10))}
                    disabled={!selectedImage}
                  >
                    <ZoomOut className="w-4 h-4" />
                  </Button>
                  <span className="text-sm min-w-[60px] text-center">{zoom}%</span>
                  <Button
                    variant="outline"
                    size="icon"
                    onClick={() => setZoom(Math.min(200, zoom + 10))}
                    disabled={!selectedImage}
                  >
                    <ZoomIn className="w-4 h-4" />
                  </Button>
                  <Button variant="outline" size="icon" disabled={!selectedImage}>
                    <Maximize2 className="w-4 h-4" />
                  </Button>
                  <Button variant="outline" size="icon" disabled={!selectedImage}>
                    <Download className="w-4 h-4" />
                  </Button>
                </div>
              </div>

              {/* Image Display / Upload Zone */}
              {selectedImage ? (
                <div className="relative bg-black rounded-xl overflow-hidden" style={{ height: '500px' }}>
                  <motion.img
                    src={selectedImage}
                    alt="MRI Scan"
                    className="w-full h-full object-contain"
                    style={{ transform: `scale(${zoom / 100})` }}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                  />
                  <Button
                    variant="destructive"
                    size="icon"
                    className="absolute top-4 right-4"
                    onClick={() => {
                      setSelectedImage(null);
                      setAnalysisResult(null);
                    }}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ) : (
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  className="border-2 border-dashed border-gray-300 dark:border-gray-700 rounded-xl p-12 text-center hover:border-blue-500 transition-colors cursor-pointer"
                  style={{ height: '500px' }}
                  onClick={() => fileInputRef.current?.click()}
                >
                  <motion.div
                    animate={{ y: [0, -10, 0] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                    className="flex flex-col items-center justify-center h-full"
                  >
                    <Upload className="w-16 h-16 text-gray-400 mb-4" />
                    <h3 className="text-xl font-semibold mb-2">Upload MRI Scan</h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-4">
                      Drag and drop your MRI scan here, or click to browse
                    </p>
                    <Button className="gap-2">
                      <FileImage className="w-4 h-4" />
                      Choose File
                    </Button>
                  </motion.div>
                </div>
              )}

              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
              />
            </Card>

            {/* Analysis Button */}
            <motion.div
              initial={{ scale: 0.9 }}
              animate={{ scale: 1 }}
              transition={{ delay: 0.4 }}
            >
              <Button
                onClick={analyzeImage}
                disabled={!selectedImage || isAnalyzing}
                className="w-full h-16 text-lg gap-3 bg-gradient-to-r from-blue-600 to-green-600 hover:from-blue-700 hover:to-green-700 shadow-xl"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-6 h-6 animate-spin" />
                    Analyzing Scan...
                  </>
                ) : (
                  <>
                    <Brain className="w-6 h-6" />
                    🔬 Analyze MRI with AI
                  </>
                )}
              </Button>
            </motion.div>

            {/* Analysis Progress */}
            <AnimatePresence>
              {isAnalyzing && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                >
                  <Card className="p-6">
                    <div className="flex items-center gap-4 mb-4">
                      <div className="relative">
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                        >
                          <Brain className="w-12 h-12 text-blue-600" />
                        </motion.div>
                        <motion.div
                          className="absolute inset-0 rounded-full bg-blue-500/20"
                          animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0, 0.5] }}
                          transition={{ repeat: Infinity, duration: 1.5 }}
                        />
                      </div>
                      <div className="flex-1">
                        <p className="font-semibold mb-2">Analyzing brain scan...</p>
                        <Progress value={analysisProgress} className="h-2" />
                      </div>
                      <span className="text-2xl font-bold text-blue-600">{analysisProgress}%</span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      AI is processing the MRI scan and detecting abnormalities...
                    </p>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Results Display */}
            <AnimatePresence>
              {analysisResult && !isAnalyzing && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-6"
                >
                  {/* Confidence Score */}
                  <Card className="p-6">
                    <div className="text-center">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Analysis Confidence</p>
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ type: "spring", duration: 0.5 }}
                        className="relative inline-block"
                      >
                        <svg className="w-32 h-32 transform -rotate-90">
                          <circle
                            cx="64"
                            cy="64"
                            r="56"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="none"
                            className="text-gray-200 dark:text-gray-700"
                          />
                          <motion.circle
                            cx="64"
                            cy="64"
                            r="56"
                            stroke="currentColor"
                            strokeWidth="8"
                            fill="none"
                            strokeLinecap="round"
                            className="text-green-600"
                            initial={{ strokeDashoffset: 352 }}
                            animate={{ strokeDashoffset: 352 - (352 * analysisResult.confidence) / 100 }}
                            transition={{ duration: 1, delay: 0.2 }}
                            style={{ strokeDasharray: 352 }}
                          />
                        </svg>
                        <div className="absolute inset-0 flex items-center justify-center">
                          <span className="text-3xl font-bold">{analysisResult.confidence}%</span>
                        </div>
                      </motion.div>
                    </div>
                  </Card>

                  {/* Findings */}
                  <Card className="p-6">
                    <h3 className="text-xl font-bold mb-4">Findings</h3>
                    <div className="space-y-3">
                      {analysisResult.findings.map((finding, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.3 + index * 0.1 }}
                          className={`flex items-start gap-3 p-4 rounded-lg ${
                            finding.type === 'normal' ? 'bg-green-50 dark:bg-green-950/20' :
                            finding.type === 'attention' ? 'bg-yellow-50 dark:bg-yellow-950/20' :
                            'bg-red-50 dark:bg-red-950/20'
                          }`}
                        >
                          {finding.type === 'normal' && <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />}
                          {finding.type === 'attention' && <AlertTriangle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />}
                          {finding.type === 'critical' && <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />}
                          <div className="flex-1">
                            <p className="font-medium">{finding.text}</p>
                            <Badge
                              variant="outline"
                              className={`mt-1 text-xs ${
                                finding.type === 'normal' ? 'border-green-600 text-green-600' :
                                finding.type === 'attention' ? 'border-yellow-600 text-yellow-600' :
                                'border-red-600 text-red-600'
                              }`}
                            >
                              Severity: {finding.severity}
                            </Badge>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </Card>

                  {/* Recommendations */}
                  <Card className="p-6">
                    <h3 className="text-xl font-bold mb-4">Recommendations</h3>
                    <div className="space-y-2">
                      {analysisResult.recommendations.map((rec, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: 0.6 + index * 0.1 }}
                          className="flex items-start gap-3 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg"
                        >
                          <div className="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm flex-shrink-0 mt-0.5">
                            {index + 1}
                          </div>
                          <p className="text-sm">{rec}</p>
                        </motion.div>
                      ))}
                    </div>
                  </Card>

                  {/* Export Report Button */}
                  <Button className="w-full gap-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">
                    <Download className="w-4 h-4" />
                    Export Complete Report (PDF)
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>
    </DoctorLayout>
  );
}
