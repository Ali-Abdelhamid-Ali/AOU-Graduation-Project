import { useState } from 'react';
import PatientLayout from '../components/PatientLayout';
import { 
  Calendar, 
  FileText, 
  Pill,
  Heart,
  Activity,
  Clock,
  AlertCircle,
  CheckCircle2,
  Plus,
  Eye,
  Download,
  MessageSquare,
  TrendingUp,
  Thermometer,
  Droplet,
  Brain
} from 'lucide-react';
import { Card } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';
import { Progress } from '../components/ui/progress';
import { motion } from 'motion/react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Calendar as CalendarComponent } from '../components/ui/calendar';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const upcomingAppointments = [
  {
    id: 1,
    doctor: 'Dr. Sarah Ahmed',
    specialty: 'Neurologist',
    date: '2024-02-08',
    time: '10:00 AM',
    type: 'MRI Review',
    status: 'confirmed',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=doctor',
  },
  {
    id: 2,
    doctor: 'Dr. Mohammed Ali',
    specialty: 'Cardiologist',
    date: '2024-02-15',
    time: '2:30 PM',
    type: 'Regular Checkup',
    status: 'pending',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=doctor2',
  },
];

const medications = [
  { id: 1, name: 'Aspirin', dosage: '100mg', frequency: 'Once daily', time: '08:00 AM', taken: true },
  { id: 2, name: 'Lisinopril', dosage: '10mg', frequency: 'Once daily', time: '08:00 AM', taken: true },
  { id: 3, name: 'Metformin', dosage: '500mg', frequency: 'Twice daily', time: '06:00 PM', taken: false },
];

const recentTests = [
  { id: 1, name: 'Complete Blood Count', date: '2024-01-30', status: 'available', type: 'Lab' },
  { id: 2, name: 'MRI Brain Scan', date: '2024-01-25', status: 'available', type: 'Imaging' },
  { id: 3, name: 'ECG Test', date: '2024-01-20', status: 'available', type: 'Cardiac' },
];

const vitalsTrend = [
  { date: 'Jan 1', bp: 120, hr: 72, temp: 36.8 },
  { date: 'Jan 8', bp: 118, hr: 70, temp: 37.0 },
  { date: 'Jan 15', bp: 122, hr: 74, temp: 36.9 },
  { date: 'Jan 22', bp: 119, hr: 71, temp: 37.1 },
  { date: 'Jan 29', bp: 121, hr: 73, temp: 36.8 },
  { date: 'Today', bp: 120, hr: 72, temp: 37.2 },
];

const healthTips = [
  { icon: Heart, title: 'Stay Hydrated', description: 'Drink at least 8 glasses of water daily', color: 'from-blue-500 to-cyan-500' },
  { icon: Activity, title: 'Exercise Regularly', description: '30 minutes of physical activity', color: 'from-green-500 to-emerald-500' },
  { icon: Pill, title: 'Take Medications', description: 'Don\'t miss your scheduled doses', color: 'from-purple-500 to-pink-500' },
];

export default function PatientDashboard() {
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const [selectedDoctor, setSelectedDoctor] = useState('');
  const [selectedTime, setSelectedTime] = useState('');

  const handleBookAppointment = () => {
    if (!selectedDate || !selectedDoctor || !selectedTime) {
      toast.error('Please fill all fields');
      return;
    }
    toast.success('Appointment booked successfully!');
  };

  return (
    <PatientLayout>
      <div className="space-y-8">
        {/* Welcome Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-bold mb-2">Welcome back, Ahmed! 👋</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Here's an overview of your health status
          </p>
        </motion.div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Dialog>
              <DialogTrigger asChild>
                <Card className="p-6 cursor-pointer hover:shadow-xl transition-all group">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                      <Calendar className="w-7 h-7 text-white" />
                    </div>
                    <div>
                      <h3 className="font-bold">Book Appointment</h3>
                      <p className="text-sm text-gray-600 dark:text-gray-400">Schedule a visit</p>
                    </div>
                  </div>
                </Card>
              </DialogTrigger>
              <DialogContent className="max-w-2xl">
                <DialogHeader>
                  <DialogTitle>Book New Appointment</DialogTitle>
                  <DialogDescription>
                    Select your preferred doctor, date, and time
                  </DialogDescription>
                </DialogHeader>
                <div className="space-y-6 py-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Select Doctor</label>
                    <Select value={selectedDoctor} onValueChange={setSelectedDoctor}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose a doctor" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="dr-sarah">Dr. Sarah Ahmed - Neurologist</SelectItem>
                        <SelectItem value="dr-mohammed">Dr. Mohammed Ali - Cardiologist</SelectItem>
                        <SelectItem value="dr-fatima">Dr. Fatima Hassan - General Physician</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">Select Date</label>
                    <CalendarComponent
                      mode="single"
                      selected={selectedDate}
                      onSelect={setSelectedDate}
                      className="rounded-md border"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-2 block">Select Time</label>
                    <Select value={selectedTime} onValueChange={setSelectedTime}>
                      <SelectTrigger>
                        <SelectValue placeholder="Choose a time slot" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="09:00">09:00 AM</SelectItem>
                        <SelectItem value="10:00">10:00 AM</SelectItem>
                        <SelectItem value="11:00">11:00 AM</SelectItem>
                        <SelectItem value="14:00">02:00 PM</SelectItem>
                        <SelectItem value="15:00">03:00 PM</SelectItem>
                        <SelectItem value="16:00">04:00 PM</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <Button onClick={handleBookAppointment} className="w-full gap-2">
                    <Plus className="w-4 h-4" />
                    Confirm Booking
                  </Button>
                </div>
              </DialogContent>
            </Dialog>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="p-6 cursor-pointer hover:shadow-xl transition-all group">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <FileText className="w-7 h-7 text-white" />
                </div>
                <div>
                  <h3 className="font-bold">View Records</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Medical history</p>
                </div>
              </div>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card className="p-6 cursor-pointer hover:shadow-xl transition-all group">
              <div className="flex items-center gap-4">
                <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <MessageSquare className="w-7 h-7 text-white" />
                </div>
                <div>
                  <h3 className="font-bold">Contact Doctor</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">Send a message</p>
                  <Badge className="mt-1 bg-red-500 text-white">2 new</Badge>
                </div>
              </div>
            </Card>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Upcoming Appointments */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Card className="p-6">
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <h2 className="text-xl font-bold mb-1">Upcoming Appointments</h2>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      You have {upcomingAppointments.length} appointments scheduled
                    </p>
                  </div>
                </div>

                <div className="space-y-4">
                  {upcomingAppointments.map((appointment, index) => (
                    <motion.div
                      key={appointment.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.5 + index * 0.1 }}
                      className="flex items-center gap-4 p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 hover:shadow-md transition-all border border-transparent hover:border-blue-200 dark:hover:border-blue-800"
                    >
                      <Avatar className="w-14 h-14">
                        <AvatarImage src={appointment.avatar} />
                        <AvatarFallback>{appointment.doctor[0]}</AvatarFallback>
                      </Avatar>
                      
                      <div className="flex-1">
                        <h4 className="font-semibold">{appointment.doctor}</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{appointment.specialty}</p>
                        <p className="text-xs text-gray-500 mt-1">{appointment.type}</p>
                      </div>

                      <div className="text-right">
                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-1">
                          <Calendar className="w-4 h-4" />
                          {appointment.date}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-2">
                          <Clock className="w-4 h-4" />
                          {appointment.time}
                        </div>
                        <Badge
                          variant={appointment.status === 'confirmed' ? 'default' : 'outline'}
                          className="gap-1"
                        >
                          {appointment.status === 'confirmed' && <CheckCircle2 className="w-3 h-3" />}
                          {appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1)}
                        </Badge>
                      </div>

                      <div className="flex flex-col gap-2">
                        <Button size="sm" variant="outline">
                          Reschedule
                        </Button>
                        <Button size="sm" variant="ghost" className="text-red-600">
                          Cancel
                        </Button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </Card>
            </motion.div>

            {/* Recent Test Results */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 }}
            >
              <Card className="p-6">
                <h2 className="text-xl font-bold mb-4">Recent Test Results</h2>
                <div className="space-y-3">
                  {recentTests.map((test, index) => (
                    <motion.div
                      key={test.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.7 + index * 0.1 }}
                      className="flex items-center gap-4 p-4 rounded-lg bg-gray-50 dark:bg-gray-800/50 hover:shadow-md transition-all"
                    >
                      <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
                        test.type === 'Lab' ? 'bg-blue-100 dark:bg-blue-900/20' :
                        test.type === 'Imaging' ? 'bg-purple-100 dark:bg-purple-900/20' :
                        'bg-red-100 dark:bg-red-900/20'
                      }`}>
                        {test.type === 'Lab' && <Droplet className="w-6 h-6 text-blue-600" />}
                        {test.type === 'Imaging' && <Brain className="w-6 h-6 text-purple-600" />}
                        {test.type === 'Cardiac' && <Heart className="w-6 h-6 text-red-600" />}
                      </div>
                      
                      <div className="flex-1">
                        <h4 className="font-semibold">{test.name}</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">{test.date}</p>
                      </div>

                      <Badge variant="secondary" className="gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        Available
                      </Badge>

                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" className="gap-2">
                          <Eye className="w-4 h-4" />
                          View
                        </Button>
                        <Button size="sm" variant="ghost" className="gap-2">
                          <Download className="w-4 h-4" />
                        </Button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </Card>
            </motion.div>

            {/* Vitals Trend */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
            >
              <Card className="p-6">
                <h2 className="text-xl font-bold mb-4">Vitals Trend</h2>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={vitalsTrend}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                    <XAxis dataKey="date" stroke="#6B7280" />
                    <YAxis stroke="#6B7280" />
                    <Tooltip />
                    <Line type="monotone" dataKey="bp" stroke="#2563EB" strokeWidth={3} name="Blood Pressure" />
                    <Line type="monotone" dataKey="hr" stroke="#10B981" strokeWidth={3} name="Heart Rate" />
                  </LineChart>
                </ResponsiveContainer>
              </Card>
            </motion.div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Medication Tracker */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5 }}
            >
              <Card className="p-6">
                <h3 className="text-lg font-bold mb-4">Today's Medications</h3>
                <div className="space-y-3">
                  {medications.map((med) => (
                    <div
                      key={med.id}
                      className={`p-3 rounded-lg border-2 transition-all ${
                        med.taken 
                          ? 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800' 
                          : 'bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <h4 className="font-semibold text-sm">{med.name}</h4>
                          <p className="text-xs text-gray-600 dark:text-gray-400">{med.dosage}</p>
                        </div>
                        {med.taken ? (
                          <CheckCircle2 className="w-5 h-5 text-green-600" />
                        ) : (
                          <div className="w-5 h-5 rounded-full border-2 border-gray-400" />
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-400">
                        <Clock className="w-3 h-3" />
                        {med.time} • {med.frequency}
                      </div>
                    </div>
                  ))}
                </div>
                <Button className="w-full mt-4 gap-2" variant="outline">
                  <Plus className="w-4 h-4" />
                  Add Reminder
                </Button>
              </Card>
            </motion.div>

            {/* Health Tips */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 }}
            >
              <Card className="p-6">
                <h3 className="text-lg font-bold mb-4">Health Tips</h3>
                <div className="space-y-3">
                  {healthTips.map((tip, index) => (
                    <motion.div
                      key={index}
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: 0.7 + index * 0.1 }}
                      className="p-4 rounded-xl bg-gradient-to-br from-gray-50 to-white dark:from-gray-800/50 dark:to-gray-900/50 border border-gray-200 dark:border-gray-700"
                    >
                      <div className="flex items-start gap-3">
                        <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${tip.color} flex items-center justify-center flex-shrink-0`}>
                          <tip.icon className="w-5 h-5 text-white" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-sm mb-1">{tip.title}</h4>
                          <p className="text-xs text-gray-600 dark:text-gray-400">{tip.description}</p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </Card>
            </motion.div>

            {/* Current Health Summary */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.7 }}
            >
              <Card className="p-6">
                <h3 className="text-lg font-bold mb-4">Current Health</h3>
                <div className="space-y-4">
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-600 dark:text-gray-400">Overall Health</span>
                      <span className="text-sm font-semibold text-green-600">Good</span>
                    </div>
                    <Progress value={85} className="h-2" />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div className="p-3 bg-red-50 dark:bg-red-950/20 rounded-lg">
                      <Heart className="w-5 h-5 text-red-600 mb-1" />
                      <p className="text-xs text-gray-600 dark:text-gray-400">Heart Rate</p>
                      <p className="text-lg font-bold text-red-600">72 bpm</p>
                    </div>
                    <div className="p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                      <Activity className="w-5 h-5 text-blue-600 mb-1" />
                      <p className="text-xs text-gray-600 dark:text-gray-400">BP</p>
                      <p className="text-lg font-bold text-blue-600">120/80</p>
                    </div>
                    <div className="p-3 bg-orange-50 dark:bg-orange-950/20 rounded-lg col-span-2">
                      <Thermometer className="w-5 h-5 text-orange-600 mb-1" />
                      <p className="text-xs text-gray-600 dark:text-gray-400">Temperature</p>
                      <p className="text-lg font-bold text-orange-600">37.2°C</p>
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          </div>
        </div>
      </div>
    </PatientLayout>
  );
}
