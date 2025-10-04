import { Loader2, Leaf } from 'lucide-react';
import { createPortal } from 'react-dom';

interface LoadingProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  variant?: 'spinner' | 'dots' | 'pulse' | 'leaves';
  text?: string;
  className?: string;
  fullScreen?: boolean;
}

export function Loading({ 
  size = 'md', 
  variant = 'spinner', 
  text, 
  className = '', 
  fullScreen = false 
}: LoadingProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
    xl: 'w-16 h-16'
  };

  const textSizeClasses = {
    sm: 'text-sm',
    md: 'text-base',
    lg: 'text-lg',
    xl: 'text-xl'
  };

  const containerClasses = fullScreen 
    ? 'fixed inset-0 bg-gradient-to-b from-green-50/90 to-green-100/90 backdrop-blur-sm z-[9999] flex items-center justify-center'
    : 'flex items-center justify-center';

  const renderSpinner = () => (
    <Loader2 className={`${sizeClasses[size]} text-primary animate-spin`} />
  );

  const renderDots = () => (
    <div className="flex space-x-1">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className={`${size === 'sm' ? 'w-2 h-2' : size === 'lg' ? 'w-4 h-4' : size === 'xl' ? 'w-5 h-5' : 'w-3 h-3'} bg-primary rounded-full animate-pulse`}
          style={{
            animationDelay: `${i * 0.3}s`,
            animationDuration: '1.5s'
          }}
        />
      ))}
    </div>
  );

  const renderPulse = () => (
    <div className={`${sizeClasses[size]} bg-primary/20 rounded-full animate-pulse flex items-center justify-center`}>
      <div className={`${size === 'sm' ? 'w-2 h-2' : size === 'lg' ? 'w-6 h-6' : size === 'xl' ? 'w-8 h-8' : 'w-4 h-4'} bg-primary rounded-full animate-ping`} />
    </div>
  );

  const renderLeaves = () => (
    <div className="relative">
      <div className="flex items-center justify-center">
        {[0, 1, 2, 3].map((i) => (
          <Leaf
            key={i}
            className={`${sizeClasses[size]} text-primary absolute animate-spin`}
            style={{
              transform: `rotate(${i * 90}deg)`,
              animationDuration: '2s',
              animationDelay: `${i * 0.2}s`
            }}
          />
        ))}
      </div>
    </div>
  );

  const renderLoadingAnimation = () => {
    switch (variant) {
      case 'dots':
        return renderDots();
      case 'pulse':
        return renderPulse();
      case 'leaves':
        return renderLeaves();
      default:
        return renderSpinner();
    }
  };

  return (
    <div 
      className={`${containerClasses} ${className}`}
      style={fullScreen ? { 
        position: 'fixed', 
        top: 0, 
        left: 0, 
        right: 0, 
        bottom: 0,
        zIndex: 9999
      } : {}}
    >
      <div className="flex flex-col items-center space-y-4">
        {renderLoadingAnimation()}
        {text && (
          <p className={`${textSizeClasses[size]} text-primary/80 animate-pulse`}>
            {text}
          </p>
        )}
      </div>
    </div>
  );
}

// Preset loading components for common use cases
export function PageLoading() {
  const loadingElement = (
    <Loading
      fullScreen
      size="lg"
      variant="leaves"
      text="Growing your experience..."
      className="min-h-screen"
    />
  );

  // Use portal to render at document body level for guaranteed full-screen
  if (typeof document !== 'undefined') {
    return createPortal(loadingElement, document.body);
  }
  
  return loadingElement;
}

// Alternative full-screen loader that uses portal
export function FullScreenLoading({ text }: { text?: string }) {
  const loadingElement = (
    <div 
      className="fixed inset-0 bg-gradient-to-b from-green-50/95 to-green-100/95 backdrop-blur-sm flex items-center justify-center"
      style={{ zIndex: 99999 }}
    >
      <div className="flex flex-col items-center space-y-6">
        <div className="relative">
          {[0, 1, 2, 3].map((i) => (
            <Leaf
              key={i}
              className="w-12 h-12 text-primary absolute animate-spin"
              style={{
                transform: `rotate(${i * 90}deg)`,
                animationDuration: '2s',
                animationDelay: `${i * 0.2}s`
              }}
            />
          ))}
        </div>
        {text && (
          <p className="text-lg text-primary/80 animate-pulse font-medium">
            {text}
          </p>
        )}
      </div>
    </div>
  );

  if (typeof document !== 'undefined') {
    return createPortal(loadingElement, document.body);
  }
  
  return loadingElement;
}

export function ButtonLoading() {
  return (
    <Loading
      size="sm"
      variant="spinner"
      className="mr-2"
    />
  );
}

export function SectionLoading({ text }: { text?: string }) {
  return (
    <div className="py-12">
      <Loading
        size="md"
        variant="pulse"
        text={text || "Cultivating data..."}
      />
    </div>
  );
}

export function InlineLoading() {
  return (
    <Loading
      size="sm"
      variant="dots"
      className="inline-flex"
    />
  );
}