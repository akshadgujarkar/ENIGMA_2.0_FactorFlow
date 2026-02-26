import { motion } from 'framer-motion';

interface RadialProgressProps {
  value: number;
  size?: number;
  strokeWidth?: number;
  color: string;
  label: string;
  icon?: React.ReactNode;
  inverted?: boolean;
}

export function RadialProgress({
  value,
  size = 90,
  strokeWidth = 7,
  color,
  label,
  icon,
  inverted = false,
}: RadialProgressProps) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = Math.min(value / 100, 1);
  const offset = circumference * (1 - progress);

  const getStatus = () => {
    if (inverted) {
      if (value <= 30) return { label: 'Good', className: 'indicator-badge-good' };
      if (value <= 60) return { label: 'Warning', className: 'indicator-badge-warning' };
      return { label: 'Critical', className: 'indicator-badge-critical' };
    }
    if (value >= 70) return { label: 'Good', className: 'indicator-badge-good' };
    if (value >= 40) return { label: 'Warning', className: 'indicator-badge-warning' };
    return { label: 'Critical', className: 'indicator-badge-critical' };
  };

  const status = getStatus();

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className="relative" style={{ width: size, height: size }}>
        <svg className="transform -rotate-90" width={size} height={size}>
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="hsl(var(--muted))"
            strokeWidth={strokeWidth}
          />
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeLinecap="round"
            initial={{ strokeDashoffset: circumference }}
            animate={{ strokeDashoffset: offset }}
            transition={{ duration: 0.8, ease: 'easeOut' }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          {icon && <span className="mb-0.5 opacity-60">{icon}</span>}
          <span className="text-lg font-bold mono text-foreground">{value}</span>
        </div>
      </div>
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <span className={status.className}>{status.label}</span>
    </div>
  );
}
