import { useState, useEffect } from 'react';
import { Link } from 'react-router';
import DoctorLayout from '@/components/layout/FIGMA/DoctorLayout';
import { 
  Users, 
  AlertCircle, 
  Calendar, 
  TrendingUp,
  Clock,
  Brain,
  Activity,
  MessageSquare,
  FileText,
  ArrowRight,
  CheckCircle2,
  XCircle
} from 'lucide-react';
import { Card } from '@/components/ui/FIGMA/card';
import { Button } from '@/components/ui/FIGMA/button';
import { Badge } from '@/components/ui/FIGMA/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/FIGMA/avatar';
import { motion } from 'framer-motion';
import { LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Mock data
const statsData = [
  { icon: Users, label: 'Today\'s Patients', value: 24, change: '+12%', color: 'from-blue-500 to-blue-600' },
  { icon: AlertCircle, label: 'Emergency Cases', value: 3, change: '-25%', color: 'from-red-500 to-red-600' },
  { icon: Calendar, label: 'Appointments', value: 18, change: '+8%', color: 'from-green-500 to-green-600' },
  { icon: TrendingUp, label: 'Satisfaction', value: 98, change: '+2%', color: 'from-purple-500 to-purple-600', suffix: '%' },
];

const todayAppointments = [
  {
    id: 1,
    patient: 'Ahmed Hassan',
    time: '09:00 AM',
    type: 'MRI Analysis',
    status: 'confirmed',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ahmed',
  },
  {
    id: 2,
    patient: 'Fatima Ali',
    time: '10:30 AM',
    type: 'ECG Check-up',
    status: 'pending',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Fatima',
  },
  {
    id: 3,
    patient: 'Mohammed Salah',
    time: '11:45 AM',
    type: 'Follow-up',
    status: 'confirmed',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Mohammed',
  },
  {
    id: 4,
    patient: 'Sara Ibrahim',
    time: '02:00 PM',
    type: 'Initial Consultation',
    status: 'confirmed',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sara',
  },
  {
    id: 5,
    patient: 'Omar Khaled',
    time: '03:30 PM',
    type: 'MRI Review',
    status: 'completed',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Omar',
  },
];

const chartData = [
  { name: 'Mon', patients: 20 },
  { name: 'Tue', patients: 25 },
  { name: 'Wed', patients: 22 },
  { name: 'Thu', patients: 28 },
  { name: 'Fri', patients: 24 },
  { name: 'Sat', patients: 15 },
  { name: 'Sun', patients: 10 },
];

function AnimatedCounter({ value, suffix = '' }: { value: number; suffix?: string }) {
  const [count, setCount] = useState(0);

  useEffect(() => {
    const duration = 1500;
    const steps = 60;
    const increment = value / steps;
    let current = 0;

    const timer = setInterval(() => {
      current += increment;
      if (current >= value) {
        setCount(value);
        clearInterval(timer);
      } else {
        setCount(Math.floor(current));
      }
    }, duration / steps);

    return () => clearInterval(timer);
  }, [value]);

  return <span>{count}{suffix}</span>;
}

export default function DoctorDashboard() {
  return (
    <DoctorLayout>
      <div className="p-8 space-y-8">
        {/* Welcome Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-bold mb-2">Welcome back, Dr. Sarah 👋</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Here's what's happening with your patients today
          </p>
        </motion.div>

        {/* Statistics Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statsData.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <Card className="relative overflow-hidden group hover:shadow-xl transition-all duration-300 cursor-pointer">
                <motion.div
                  className="absolute inset-0 bg-gradient-to-br opacity-0 group-hover:opacity-10 transition-opacity"
                  style={{ background: `linear-gradient(to bottom right, var(--tw-gradient-stops))` }}
                />
                <div className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${stat.color} flex items-center justify-center shadow-lg`}>
                      <stat.icon className="w-7 h-7 text-white" />
                    </div>
                    <Badge variant={stat.change.startsWith('+') ? 'default' : 'destructive'} className="text-xs">
                      {stat.change}
                    </Badge>
                  </div>
                  <div>
                    <p className="text-gray-600 dark:text-gray-400 text-sm mb-1">{stat.label}</p>
                    <p className="text-3xl font-bold">
                      <AnimatedCounter value={stat.value} suffix={stat.suffix} />
                    </p>
                  </div>
                </div>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Today's Appointments */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
            className="lg:col-span-2"
          >
            <Card className="p-6">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold mb-1">Today's Appointments</h2>
                  <p className="text-sm text-gray-600 dark:text-gray-400">You have {todayAppointments.length} appointments today</p>
                </div>
                <Button variant="outline" className="gap-2">
                  View All
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </div>

              <div className="space-y-4">
                {todayAppointments.map((appointment, index) => (
                  <motion.div
                    key={appointment.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: 0.5 + index * 0.1 }}
                    whileHover={{ scale: 1.02, x: 4 }}
                    className="flex items-center gap-4 p-4 rounded-xl bg-gray-50 dark:bg-gray-800/50 hover:shadow-md transition-all cursor-pointer border border-transparent hover:border-blue-200 dark:hover:border-blue-800"
                  >
                    <Avatar className="w-12 h-12">
                      <AvatarImage src={appointment.avatar} />
                      <AvatarFallback>{appointment.patient[0]}</AvatarFallback>
                    </Avatar>
                    
                    <div className="flex-1">
                      <h4 className="font-semibold">{appointment.patient}</h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400">{appointment.type}</p>
                    </div>

                    <div className="text-right">
                      <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400 mb-1">
                        <Clock className="w-4 h-4" />
                        {appointment.time}
                      </div>
                      <Badge
                        variant={
                          appointment.status === 'confirmed' ? 'default' :
                          appointment.status === 'completed' ? 'secondary' :
                          'outline'
                        }
                        className="gap-1"
                      >
                        {appointment.status === 'completed' && <CheckCircle2 className="w-3 h-3" />}
                        {appointment.status === 'cancelled' && <XCircle className="w-3 h-3" />}
                        {appointment.status.charAt(0).toUpperCase() + appointment.status.slice(1)}
                      </Badge>
                    </div>

                    <Button size="sm" variant="ghost" className="gap-2">
                      View
                      <ArrowRight className="w-4 h-4" />
                    </Button>
                  </motion.div>
                ))}
              </div>
            </Card>
          </motion.div>

          {/* Quick Actions */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            className="space-y-6"
          >
            {/* Quick Actions Card */}
            <Card className="p-6">
              <h3 className="text-lg font-bold mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <Link to="/mri-analysis">
                  <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                    <Button className="w-full justify-start gap-3 h-auto py-4 bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-lg shadow-blue-500/30">
                      <Brain className="w-5 h-5" />
                      <span>New MRI Analysis</span>
                    </Button>
                  </motion.div>
                </Link>
                
                <Link to="/ecg-analysis">
                  <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                    <Button className="w-full justify-start gap-3 h-auto py-4 bg-gradient-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 shadow-lg shadow-green-500/30">
                      <Activity className="w-5 h-5" />
                      <span>ECG Analysis</span>
                    </Button>
                  </motion.div>
                </Link>

                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button variant="outline" className="w-full justify-start gap-3 h-auto py-4">
                    <MessageSquare className="w-5 h-5" />
                    <span>Messages</span>
                    <Badge className="ml-auto">3</Badge>
                  </Button>
                </motion.div>

                <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                  <Button variant="outline" className="w-full justify-start gap-3 h-auto py-4">
                    <FileText className="w-5 h-5" />
                    <span>Generate Report</span>
                  </Button>
                </motion.div>
              </div>
            </Card>

            {/* Recent Activity */}
            <Card className="p-6">
              <h3 className="text-lg font-bold mb-4">Recent Activity</h3>
              <div className="space-y-4">
                {[
                  { text: 'MRI scan analyzed for Ahmed H.', time: '10 min ago', type: 'success' },
                  { text: 'New appointment scheduled', time: '1 hour ago', type: 'info' },
                  { text: 'Lab results received', time: '2 hours ago', type: 'warning' },
                ].map((activity, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 + index * 0.1 }}
                    className="flex gap-3"
                  >
                    <div className={`w-2 h-2 rounded-full mt-2 ${
                      activity.type === 'success' ? 'bg-green-500' :
                      activity.type === 'warning' ? 'bg-yellow-500' :
                      'bg-blue-500'
                    }`} />
                    <div className="flex-1">
                      <p className="text-sm">{activity.text}</p>
                      <p className="text-xs text-gray-500">{activity.time}</p>
                    </div>
                  </motion.div>
                ))}
              </div>
            </Card>
          </motion.div>
        </div>

        {/* Patient Analytics Chart */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.8 }}
        >
          <Card className="p-6">
            <h2 className="text-xl font-bold mb-6">Weekly Patient Overview</h2>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorPatients" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                <XAxis dataKey="name" stroke="#6B7280" />
                <YAxis stroke="#6B7280" />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#fff', 
                    border: '1px solid #E5E7EB', 
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="patients" 
                  stroke="#2563EB" 
                  strokeWidth={3}
                  fillOpacity={1} 
                  fill="url(#colorPatients)" 
                />
              </AreaChart>
            </ResponsiveContainer>
          </Card>
        </motion.div>
      </div>
    </DoctorLayout>
  );
}
