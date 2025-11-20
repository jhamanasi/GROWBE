# Growbe Frontend - Next.js Financial Advisor Interface

<p align="center">
  <img src="https://img.shields.io/badge/React-19+-61dafb.svg" alt="React Version">
  <img src="https://img.shields.io/badge/Next.js-15+-000000.svg" alt="Next.js Version">
  <img src="https://img.shields.io/badge/TypeScript-5+-3178c6.svg" alt="TypeScript">
  <img src="https://img.shields.io/badge/Tailwind_CSS-4+-38bdf8.svg" alt="Tailwind CSS">
</p>

The frontend interface for **Growbe** - an AI-powered financial advisory platform built with modern React technologies.

## 🌟 Features

### 🎨 Modern UI/UX
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **Dark/Light Themes**: Automatic theme switching with system preferences
- **Smooth Animations**: Framer Motion powered transitions and interactions
- **Accessible**: WCAG compliant with keyboard navigation and screen reader support

### 💬 Real-time Chat Interface
- **Streaming Responses**: See AI responses appear in real-time
- **Rich Content Display**: Mathematical formulas with KaTeX rendering
- **Interactive Charts**: Embedded Chart.js visualizations
- **Conversation History**: Persistent chat sessions with search and filtering

### 📊 Financial Data Visualization
- **Calculation Breakdowns**: Step-by-step math explanations
- **SQL Query Results**: Formatted database query outputs
- **Chart Integrations**: Bar charts, pie charts, line graphs
- **Financial Dashboards**: Comprehensive data displays

### 🔧 Developer Experience
- **TypeScript**: Full type safety and IntelliSense
- **Hot Reload**: Instant updates during development
- **Component Library**: Reusable UI components with shadcn/ui
- **Modern Tooling**: ESLint, Prettier, and optimized build pipeline

## 🚀 Quick Start

### Prerequisites
- **Node.js 18+** with npm
- **Backend Running**: Growbe backend must be running on port 8000

### Installation & Setup

```bash
# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env.local

# Configure API endpoint (if different from default)
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start development server
npm run dev
```

Visit `http://localhost:3001` to see Growbe in action!

## 📁 Project Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router
│   │   ├── chat/              # Main chat interface
│   │   ├── conversations/     # Conversation history
│   │   ├── financial-assessment/ # User onboarding
│   │   ├── lead-capture/      # Lead generation
│   │   ├── schema-builder/    # Advanced features
│   │   ├── globals.css        # Global styles
│   │   └── layout.tsx         # Root layout
│   ├── components/            # React components
│   │   ├── ChatWindow.tsx     # Main chat component
│   │   ├── CalculationDetailsPanel.tsx # Math displays
│   │   ├── ChartDisplay.tsx   # Chart visualizations
│   │   ├── ui/                # Reusable UI components
│   │   └── ...                # Other components
│   ├── contexts/              # React contexts
│   │   ├── AuthContext.tsx    # Authentication state
│   │   └── StreamingContext.tsx # Real-time updates
│   └── lib/                   # Utilities
│       └── utils.ts           # Helper functions
├── public/                    # Static assets
│   ├── growbe-logo.png       # Brand assets
│   └── ...                    # Icons and images
├── package.json               # Dependencies and scripts
├── tailwind.config.js         # Tailwind CSS config
├── next.config.ts            # Next.js configuration
└── tsconfig.json             # TypeScript configuration
```

## 🎯 Key Components

### Chat System
- **`ChatWindow`**: Main conversational interface with streaming
- **`StreamingContext`**: Manages real-time message updates
- **`CalculationDetailsPanel`**: Displays mathematical breakdowns
- **`ChartDisplay`**: Renders interactive financial charts

### UI Components
- **shadcn/ui**: High-quality, accessible component library
- **Tailwind CSS**: Utility-first styling framework
- **Framer Motion**: Smooth animations and transitions
- **Lucide React**: Beautiful icon library

### Data Visualization
- **Chart.js**: Flexible charting library
- **KaTeX**: Mathematical formula rendering
- **Recharts**: React charting components

## 🔧 Development

### Available Scripts

```bash
# Development
npm run dev          # Start development server (port 3001)
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
npm run type-check   # TypeScript type checking

# Testing
npm run test         # Run tests (if configured)
```

### Environment Variables

Create `.env.local` in the frontend root:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Development
NEXT_PUBLIC_ENVIRONMENT=development
NODE_ENV=development
```

### Code Style & Guidelines

- **TypeScript**: Strict type checking enabled
- **ESLint**: Airbnb config with React rules
- **Prettier**: Code formatting
- **Component Structure**: Functional components with hooks
- **State Management**: React Context for global state

### Adding New Features

1. **Create Component**: Add to `src/components/`
2. **Add Route**: Create page in `src/app/`
3. **Update Types**: Add TypeScript interfaces
4. **Style**: Use Tailwind CSS classes
5. **Test**: Verify functionality

## 🔗 API Integration

The frontend communicates with the Growbe backend via REST API:

### Key Endpoints Used
- `POST /api/conversations/start` - Initialize conversations
- `POST /api/conversations/{id}/message` - Send messages
- `GET /api/conversations/{id}/messages` - Get message history
- `GET /api/conversations` - List conversations

### Real-time Features
- **Server-Sent Events**: Streaming AI responses
- **WebSocket Support**: Future real-time updates
- **Optimistic Updates**: Immediate UI feedback

## 🎨 Design System

### Colors
- **Primary**: Growbe brand colors
- **Neutral**: Grayscale palette
- **Semantic**: Success, warning, error states

### Typography
- **Font**: Geist Sans (Next.js optimized)
- **Sizes**: Consistent scale (xs to 4xl)
- **Weights**: Regular, medium, semibold, bold

### Components
- **Buttons**: Multiple variants (primary, secondary, outline)
- **Cards**: Content containers with shadows
- **Forms**: Accessible input components
- **Modals**: Overlay dialogs and confirmations

## 📱 Responsive Design

- **Mobile First**: Optimized for mobile devices
- **Tablet Support**: Dedicated tablet breakpoints
- **Desktop Enhancement**: Additional features for larger screens
- **Touch Friendly**: Appropriate touch targets and gestures

## 🔧 Build & Deployment

### Build Process
```bash
npm run build  # Creates optimized production build
npm run start  # Serves production build
```

### Deployment Options
- **Vercel**: Recommended for Next.js apps
- **Netlify**: Alternative hosting platform
- **Docker**: Containerized deployment
- **Static Export**: For CDN deployment

### Performance Optimization
- **Code Splitting**: Automatic route-based splitting
- **Image Optimization**: Next.js built-in optimization
- **Bundle Analysis**: Webpack bundle analyzer
- **Caching**: Aggressive caching strategies

## 🐛 Troubleshooting

### Common Issues

#### "API Connection Failed"
**Solution**: Ensure backend is running on port 8000 and `NEXT_PUBLIC_API_URL` is correct

#### "Build Errors"
**Solution**: Clear cache (`rm -rf .next`) and reinstall dependencies

#### "Type Errors"
**Solution**: Run `npm run type-check` to identify TypeScript issues

#### "Styling Issues"
**Solution**: Restart dev server and check Tailwind configuration

### Development Tips

- **Hot Reload**: Changes auto-refresh in development
- **Error Overlay**: Detailed error messages in development
- **React DevTools**: Debug component state and props
- **Network Tab**: Monitor API calls and responses

## 🤝 Contributing

### Frontend Development Guidelines

1. **Component Structure**: Use functional components with TypeScript
2. **State Management**: Prefer React hooks over class components
3. **Styling**: Use Tailwind CSS utility classes
4. **Accessibility**: Ensure WCAG compliance for all components
5. **Performance**: Optimize re-renders and bundle size

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes with proper TypeScript types
3. Test on multiple screen sizes
4. Run linting: `npm run lint`
5. Submit PR with detailed description

## 📄 License

This project is licensed under the MIT License.

---

**Growbe Frontend** - The beautiful face of AI-powered financial advice. 💫
