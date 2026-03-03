import { useState, useEffect, useRef } from 'react';
import { useParams } from 'react-router';
import DoctorLayout from '../components/DoctorLayout';
import { 
  Activity, 
  Heart,
  Play,
  Pause,
  Upload,
  Download,
  Zap,
  AlertCircle,
  CheckCircle2,
  TrendingUp,
  Clock,
  Loader2
} from 'lucide-react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Progress } from '../components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { motion, AnimatePresence } from 'motion/react';
import { toast } from 'sonner';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, ReferenceLine } from 'recharts';

interface ECGAnalysisResult {
  heartRate: number;
  rhythm: string;
  abnormalities: {
    type: 'normal' | 'warning' | 'critical';
    text: string;
  }[];
  hrv: number;
  qtInterval: number;
  stSegment: string;
}

const mockPatient = {
  id: '1',
  name: 'Fatima Ali',
  age: 52,
  gender: 'Female',
  avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Fatima',
};

// Generate ECG-like waveform data
const generateECGData = (time: number, heartRate: number) => {
  const data: { time: number; value: number }[] = [];
  const beatInterval = 60 / heartRate; // seconds per beat
  
  for (let i = 0; i < 500; i++) {
    const t = (time + i * 0.01) % beatInterval;
    let value = 0;
    
    // P wave
    if (t > 0 && t < 0.08) {
      value = 0.2 * Math.sin((t / 0.08) * Math.PI);
    }
    // QRS complex
    else if (t > 0.12 && t < 0.22) {
      if (t < 0.14) {
        value = -0.3;
      } else if (t < 0.16) {
        value = 1.2;
      } else {
        value = -0.4;
      }
    }
    // T wave
    else if (t > 0.28 && t < 0.42) {
      value = 0.3 * Math.sin(((t - 0.28) / 0.14) * Math.PI);
    }
    
    // Add some noise
    value += (Math.random() - 0.5) * 0.05;
    
    data.push({ time: i, value });
  }
  
  return data;
};

const historicalData = [
  { date: 'Jan 15', hr: 72, hrv: 45 },
  { date: 'Feb 01', hr: 75, hrv: 42 },
  { date: 'Feb 15', hr: 70, hrv: 48 },
  { date: 'Mar 01', hr: 73, hrv: 46 },
  { date: 'Mar 15', hr: 71, hrv: 47 },
  { date: 'Today', hr: 72, hrv: 45 },
];

export default function ECGAnalysis() {
  const { patientId } = useParams();
  const [isRecording, setIsRecording] = useState(false);
  const [ecgData, setEcgData] = useState(generateECGData(0, 72));
  const [time, setTime] = useState(0);
  const [heartRate, setHeartRate] = useState(72);
  const [speed, setSpeed] = useState('50');
  const [selectedLead, setSelectedLead] = useState('II');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisProgress, setAnalysisProgress] = useState(0);
  const [analysisResult, setAnalysisResult] = useState<ECGAnalysisResult | null>(null);
  const animationRef = useRef<number>();

  useEffect(() => {
    if (isRecording) {
      const animate = () => {
        setTime(prev => {
          const newTime = prev + 0.01;
          setEcgData(generateECGData(newTime, heartRate));
          return newTime;
        });
        animationRef.current = requestAnimationFrame(animate);
      };
      animationRef.current = requestAnimationFrame(animate);
    } else {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    }

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isRecording, heartRate]);

  const toggleRecording = () => {
    setIsRecording(!isRecording);
    if (!isRecording) {
      toast.success('ECG recording started');
    } else {
      toast.info('ECG recording paused');
    }
  };

  const analyzeECG = async () => {
    setIsAnalyzing(true);
    setAnalysisProgress(0);

    const interval = setInterval(() => {
      setAnalysisProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 10;
      });
    }, 150);

    setTimeout(() => {
      setIsAnalyzing(false);
      setAnalysisResult({
        heartRate: 72,
        rhythm: 'Normal Sinus Rhythm',
        hrv: 45,
        qtInterval: 420,
        stSegment: 'Normal',
        abnormalities: [
          { type: 'normal', text: 'Regular rhythm detected' },
          { type: 'normal', text: 'QRS duration within normal limits' },
          { type: 'warning', text: 'Slight T-wave inversion in Lead III' },
        ],
      });
      toast.success('ECG analysis completed');
    }, 1500);
  };

  const getHeartRateColor = (hr: number) => {
    if (hr < 60) return 'text-blue-600';
    if (hr > 100) return 'text-red-600';
    return 'text-green-600';
  };

  const getHeartRateStatus = (hr: number) => {
    if (hr < 60) return 'Bradycardia';
    if (hr > 100) return 'Tachycardia';
    return 'Normal';
  };

  return (
    <DoctorLayout>
      <div className="p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-6"
        >
          <h1 className="text-3xl font-bold mb-2">ECG Analysis</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Real-time heart signal monitoring and AI-powered analysis
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Patient Info - Sidebar */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-6"
          >
            <Card className="p-6">
              <div className="flex items-center gap-4 mb-6">
                <Avatar className="w-16 h-16">
                  <AvatarImage src={mockPatient.avatar} />
                  <AvatarFallback>{mockPatient.name[0]}</AvatarFallback>
                </Avatar>
                <div>
                  <h2 className="text-lg font-bold">{mockPatient.name}</h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {mockPatient.age} years • {mockPatient.gender}
                  </p>
                </div>
              </div>

              {/* Live Heart Rate */}
              <div className="text-center p-6 bg-gradient-to-br from-red-50 to-pink-50 dark:from-red-950/20 dark:to-pink-950/20 rounded-xl mb-4">
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ repeat: Infinity, duration: 60 / heartRate }}
                >
                  <Heart className="w-16 h-16 text-red-500 mx-auto mb-2" />
                </motion.div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Heart Rate</p>
                <p className={`text-5xl font-bold ${getHeartRateColor(heartRate)}`}>
                  {heartRate}
                </p>
                <p className="text-xs text-gray-500 mt-1">BPM</p>
                <Badge 
                  variant={heartRate >= 60 && heartRate <= 100 ? 'default' : 'destructive'}
                  className="mt-2"
                >
                  {getHeartRateStatus(heartRate)}
                </Badge>
              </div>

              {/* Controls */}
              <div className="space-y-3">
                <div>
                  <label className="text-sm text-gray-600 dark:text-gray-400 mb-2 block">Lead Selection</label>
                  <Select value={selectedLead} onValueChange={setSelectedLead}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="I">Lead I</SelectItem>
                      <SelectItem value="II">Lead II</SelectItem>
                      <SelectItem value="III">Lead III</SelectItem>
                      <SelectItem value="aVR">Lead aVR</SelectItem>
                      <SelectItem value="aVL">Lead aVL</SelectItem>
                      <SelectItem value="aVF">Lead aVF</SelectItem>
                      <SelectItem value="V1">Lead V1</SelectItem>
                      <SelectItem value="V2">Lead V2</SelectItem>
                      <SelectItem value="V3">Lead V3</SelectItem>
                      <SelectItem value="V4">Lead V4</SelectItem>
                      <SelectItem value="V5">Lead V5</SelectItem>
                      <SelectItem value="V6">Lead V6</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div>
                  <label className="text-sm text-gray-600 dark:text-gray-400 mb-2 block">Speed (mm/s)</label>
                  <Select value={speed} onValueChange={setSpeed}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="25">25 mm/s</SelectItem>
                      <SelectItem value="50">50 mm/s</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <Button
                  onClick={toggleRecording}
                  className={`w-full gap-2 ${
                    isRecording 
                      ? 'bg-red-600 hover:bg-red-700' 
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {isRecording ? (
                    <>
                      <Pause className="w-4 h-4" />
                      Stop Recording
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4" />
                      Start Recording
                    </>
                  )}
                </Button>

                <Button variant="outline" className="w-full gap-2">
                  <Upload className="w-4 h-4" />
                  Upload ECG File
                </Button>
              </div>
            </Card>

            {/* Quick Stats */}
            <Card className="p-6">
              <h3 className="font-bold mb-4">Current Readings</h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                  <span className="text-sm">PR Interval</span>
                  <span className="font-bold">160 ms</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-950/20 rounded-lg">
                  <span className="text-sm">QRS Duration</span>
                  <span className="font-bold">90 ms</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-950/20 rounded-lg">
                  <span className="text-sm">QT Interval</span>
                  <span className="font-bold">420 ms</span>
                </div>
                <div className="flex items-center justify-between p-3 bg-orange-50 dark:bg-orange-950/20 rounded-lg">
                  <span className="text-sm">HRV</span>
                  <span className="font-bold">45 ms</span>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Main ECG Display */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-3 space-y-6"
          >
            {/* Live ECG Graph */}
            <Card className="p-6 bg-gray-900 dark:bg-black">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <Activity className="w-6 h-6 text-cyan-400" />
                  <div>
                    <h2 className="text-xl font-bold text-white">Live ECG Monitor</h2>
                    <p className="text-sm text-gray-400">Lead {selectedLead} • {speed} mm/s</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {isRecording && (
                    <motion.div
                      animate={{ opacity: [1, 0.3, 1] }}
                      transition={{ repeat: Infinity, duration: 1.5 }}
                      className="flex items-center gap-2 text-red-500"
                    >
                      <div className="w-3 h-3 bg-red-500 rounded-full" />
                      <span className="text-sm font-medium">Recording</span>
                    </motion.div>
                  )}
                  <Clock className="w-5 h-5 text-gray-400" />
                  <span className="text-white font-mono">{time.toFixed(1)}s</span>
                </div>
              </div>

              {/* ECG Grid and Waveform */}
              <div className="relative bg-black rounded-lg overflow-hidden border-2 border-cyan-900" style={{ height: '400px' }}>
                {/* Grid Background */}
                <svg className="absolute inset-0 w-full h-full" style={{ opacity: 0.2 }}>
                  <defs>
                    <pattern id="smallGrid" width="10" height="10" patternUnits="userSpaceOnUse">
                      <path d="M 10 0 L 0 0 0 10" fill="none" stroke="cyan" strokeWidth="0.5" />
                    </pattern>
                    <pattern id="grid" width="50" height="50" patternUnits="userSpaceOnUse">
                      <rect width="50" height="50" fill="url(#smallGrid)" />
                      <path d="M 50 0 L 0 0 0 50" fill="none" stroke="cyan" strokeWidth="1" />
                    </pattern>
                  </defs>
                  <rect width="100%" height="100%" fill="url(#grid)" />
                </svg>

                {/* ECG Waveform */}
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={ecgData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <ReferenceLine y={0} stroke="#1e3a8a" strokeWidth={1} />
                    <Line 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#00ffff" 
                      strokeWidth={2.5}
                      dot={false}
                      isAnimationActive={false}
                    />
                  </LineChart>
                </ResponsiveContainer>

                {/* Glow Effect */}
                <div className="absolute inset-0 pointer-events-none">
                  <div className="w-full h-1/2 bg-gradient-to-b from-cyan-500/10 to-transparent" />
                </div>
              </div>

              <div className="mt-4 flex items-center justify-between text-sm text-gray-400">
                <span>1 mV calibration</span>
                <span>Speed: {speed} mm/s</span>
              </div>
            </Card>

            {/* Analysis Button */}
            <Button
              onClick={analyzeECG}
              disabled={isAnalyzing || !isRecording}
              className="w-full h-16 text-lg gap-3 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 shadow-xl"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-6 h-6 animate-spin" />
                  Analyzing Signal...
                </>
              ) : (
                <>
                  <Zap className="w-6 h-6" />
                  ⚡ Analyze Heart Signal
                </>
              )}
            </Button>

            {/* Analysis Progress */}
            <AnimatePresence>
              {isAnalyzing && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                >
                  <Card className="p-6">
                    <div className="flex items-center gap-4">
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                      >
                        <Activity className="w-12 h-12 text-cyan-600" />
                      </motion.div>
                      <div className="flex-1">
                        <p className="font-semibold mb-2">Analyzing ECG signal...</p>
                        <Progress value={analysisProgress} className="h-2" />
                      </div>
                      <span className="text-2xl font-bold text-cyan-600">{analysisProgress}%</span>
                    </div>
                  </Card>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Analysis Results */}
            <AnimatePresence>
              {analysisResult && !isAnalyzing && (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  className="space-y-6"
                >
                  {/* Key Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <Card className="p-4 bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-blue-950/20 dark:to-cyan-950/20">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Heart Rate</p>
                      <p className="text-2xl font-bold text-blue-600">{analysisResult.heartRate} BPM</p>
                    </Card>
                    <Card className="p-4 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/20 dark:to-emerald-950/20">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">HRV</p>
                      <p className="text-2xl font-bold text-green-600">{analysisResult.hrv} ms</p>
                    </Card>
                    <Card className="p-4 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/20 dark:to-pink-950/20">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">QT Interval</p>
                      <p className="text-2xl font-bold text-purple-600">{analysisResult.qtInterval} ms</p>
                    </Card>
                    <Card className="p-4 bg-gradient-to-br from-orange-50 to-yellow-50 dark:from-orange-950/20 dark:to-yellow-950/20">
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">ST Segment</p>
                      <p className="text-2xl font-bold text-orange-600">{analysisResult.stSegment}</p>
                    </Card>
                  </div>

                  {/* Rhythm Classification */}
                  <Card className="p-6">
                    <h3 className="text-xl font-bold mb-4">Rhythm Classification</h3>
                    <div className="flex items-center gap-4 p-4 bg-green-50 dark:bg-green-950/20 rounded-lg">
                      <CheckCircle2 className="w-12 h-12 text-green-600" />
                      <div>
                        <p className="text-2xl font-bold text-green-600">{analysisResult.rhythm}</p>
                        <p className="text-sm text-gray-600 dark:text-gray-400">No immediate concerns detected</p>
                      </div>
                    </div>
                  </Card>

                  {/* Abnormalities */}
                  <Card className="p-6">
                    <h3 className="text-xl font-bold mb-4">Detailed Analysis</h3>
                    <div className="space-y-3">
                      {analysisResult.abnormalities.map((item, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.1 }}
                          className={`flex items-start gap-3 p-4 rounded-lg ${
                            item.type === 'normal' ? 'bg-green-50 dark:bg-green-950/20' :
                            item.type === 'warning' ? 'bg-yellow-50 dark:bg-yellow-950/20' :
                            'bg-red-50 dark:bg-red-950/20'
                          }`}
                        >
                          {item.type === 'normal' && <CheckCircle2 className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />}
                          {item.type === 'warning' && <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />}
                          {item.type === 'critical' && <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />}
                          <p className="font-medium flex-1">{item.text}</p>
                        </motion.div>
                      ))}
                    </div>
                  </Card>

                  {/* Historical Trend */}
                  <Card className="p-6">
                    <h3 className="text-xl font-bold mb-4">Historical Trend</h3>
                    <ResponsiveContainer width="100%" height={200}>
                      <LineChart data={historicalData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                        <XAxis dataKey="date" stroke="#6B7280" />
                        <YAxis stroke="#6B7280" />
                        <Line 
                          type="monotone" 
                          dataKey="hr" 
                          stroke="#2563EB" 
                          strokeWidth={3}
                          name="Heart Rate"
                        />
                        <Line 
                          type="monotone" 
                          dataKey="hrv" 
                          stroke="#10B981" 
                          strokeWidth={3}
                          name="HRV"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </Card>

                  {/* Export Button */}
                  <Button className="w-full gap-2 bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700">
                    <Download className="w-4 h-4" />
                    Export ECG Report (PDF)
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
