# Frontend

React-based web interface for the Guess the Player game. Built with Vite for fast development and optimized builds.

## Overview

The frontend provides an interactive game experience where users:
- Configure game settings (difficulty, player pool)
- View player career paths as club logo sequences
- Submit guesses with real-time feedback
- Track scores and view game statistics

## Directory Structure

```
frontend/
├── public/
│   └── vite.svg              # Favicon
├── src/
│   ├── assets/
│   │   └── react.svg         # React logo asset
│   ├── components/
│   │   ├── GameSetup.jsx     # Game configuration screen
│   │   ├── GameSetup.css
│   │   ├── GamePlay.jsx      # Main gameplay screen
│   │   ├── GamePlay.css
│   │   ├── GameResult.jsx    # Result/success screen
│   │   └── GameResult.css
│   ├── services/
│   │   └── api.js            # API client configuration
│   ├── App.jsx               # Main application component
│   ├── App.css               # Global app styles
│   ├── main.jsx              # Application entry point
│   └── index.css             # Base CSS reset/styles
├── index.html                # HTML template
├── vite.config.js            # Vite configuration
├── eslint.config.js          # ESLint configuration
├── package.json
└── package-lock.json
```

## Components

### App.jsx

Main application component managing game state:

**States:**
- `setup` - Game configuration screen
- `playing` - Active gameplay
- `result` - Correct guess result screen

**State Management:**
```javascript
const [gameState, setGameState] = useState('setup');
const [sessionId, setSessionId] = useState(null);
const [currentQuestion, setCurrentQuestion] = useState(null);
const [score, setScore] = useState(0);
const [totalAttempts, setTotalAttempts] = useState(0);
const [lastGuessResult, setLastGuessResult] = useState(null);
```

**Key Functions:**
- `handleStartGame(difficulty, topN)` - Initializes new session
- `handleGuess(guess)` - Submits player guess
- `handleNextQuestion(difficulty, topN)` - Fetches next question
- `handleEndGame()` - Terminates current session

### GameSetup.jsx

Configuration screen for starting new games.

**Features:**
- Difficulty selection (Short/Moderate/Long careers)
- Player pool size selection (Top 50-1000 players)
- How-to-play instructions

**Props:**
```javascript
{
  onStart: (difficulty, topN) => void,
  loading: boolean
}
```

### GamePlay.jsx

Main gameplay screen showing the career path.

**Features:**
- Club logo sequence display with arrows
- Season information for each club
- Guess input field with submit button
- Wrong guess feedback with similarity score
- Question metadata (number of clubs, shared paths)

**Props:**
```javascript
{
  question: Question,
  onGuess: (guess) => void,
  lastGuessResult: GuessResult | null,
  loading: boolean,
  onEndGame: () => void
}
```

**Question Structure:**
```javascript
{
  player_id: "12345",
  difficulty: "short",
  num_moves: 3,
  shared_by: 1,
  clubs: [
    { club: "Barcelona", logo: "https://...", season: "2020/21" },
    { club: "PSG", logo: "https://...", season: "2021/22" }
  ]
}
```

### GameResult.jsx

Success screen shown after correct guess.

**Features:**
- Player reveal with image
- Other players with same career path (if any)
- Score summary (correct/total/accuracy)
- Next question settings (can change difficulty)
- Continue/End game options

**Props:**
```javascript
{
  result: GuessResult,
  score: number,
  totalAttempts: number,
  currentDifficulty: string,
  currentTopN: number,
  onNextQuestion: (difficulty?, topN?) => void,
  onEndGame: () => void,
  loading: boolean
}
```

## API Client

### Configuration (`services/api.js`)

Axios-based API client with interceptors for logging and error handling.

```javascript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000
});
```

### Session API

```javascript
sessionAPI.startSession(difficulty, topN)
sessionAPI.submitGuess(sessionId, guess)
sessionAPI.getNextQuestion(sessionId, difficulty?, topN?)
sessionAPI.endSession(sessionId)
sessionAPI.getStatus(sessionId)
```

### Game API

```javascript
gameAPI.getStats()
```

## Styling

### Design System

**Colors:**
- Primary: `#667eea` (Purple-blue gradient start)
- Secondary: `#764ba2` (Purple gradient end)
- Success: `#2ecc71` (Green)
- Error: `#ff4757` (Red)
- Background: Linear gradient

**Typography:**
- Font Family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif
- Headers: Bold, colored
- Body: Regular weight

### Responsive Breakpoints

```css
@media (max-width: 768px) {
  /* Mobile styles */
  .clubs-grid { flex-direction: column; }
  .arrow { transform: rotate(90deg); }
}

@media (min-width: 1200px) {
  /* Large screen styles */
  .game-play { max-width: 1300px; }
}
```

### Component Styling

Each component has its own CSS file with scoped styles:
- `GameSetup.css` - Setup form styling
- `GamePlay.css` - Game board styling
- `GameResult.css` - Result screen styling
- `App.css` - Global layout and utilities

## Development

### Running Locally

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Or using make
make frontend
```

The dev server runs on `http://localhost:5173` with hot module replacement.

### Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000
```

For production:
```env
VITE_API_URL=https://your-api-domain.com
```

### Build for Production

```bash
npm run build
```

Output is generated in `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

### Linting

```bash
npm run lint
```

## Vite Configuration

### Proxy Setup (Development)

```javascript
// vite.config.js
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/session': { target: 'http://localhost:8000', changeOrigin: true },
      '/game': { target: 'http://localhost:8000', changeOrigin: true },
      '/static': { target: 'http://localhost:8000', changeOrigin: true }
    }
  }
})
```

## Game Flow

```
┌─────────────────┐
│   Game Setup    │
│  - Difficulty   │
│  - Player Pool  │
└────────┬────────┘
         │ Start Game
         ▼
┌─────────────────┐
│   Game Play     │◀──────────┐
│  - Club Logos   │           │
│  - Guess Input  │           │
└────────┬────────┘           │
         │ Correct Guess      │ Next Question
         ▼                    │
┌─────────────────┐           │
│  Game Result    │───────────┘
│  - Player Info  │
│  - Score Stats  │
│  - Settings     │
└────────┬────────┘
         │ End Game
         ▼
┌─────────────────┐
│   Game Setup    │
└─────────────────┘
```

## Error Handling

### API Errors

```javascript
try {
  const result = await sessionAPI.submitGuess(sessionId, guess);
} catch (err) {
  if (err.response?.status === 429) {
    // Rate limit handling
    const retryAfter = err.response.data.retry_after || 60;
    setError(`Too many guesses! Wait ${retryAfter} seconds.`);
  } else {
    setError('Failed to submit guess: ' + err.message);
  }
}
```

### Image Fallbacks

```javascript
const handleImageError = (e) => {
  e.target.src = '/static/images/placeholders/default-club.png';
};

<img src={club.logo} onError={handleImageError} />
```

## Dependencies

### Production
- **react** ^19.2.0 - UI framework
- **react-dom** ^19.2.0 - React DOM bindings
- **axios** ^1.13.2 - HTTP client
- **lucide-react** ^0.553.0 - Icon library

### Development
- **vite** ^7.2.2 - Build tool
- **@vitejs/plugin-react** ^5.1.0 - React plugin for Vite
- **eslint** ^9.39.1 - Linter
- **eslint-plugin-react-hooks** ^7.0.1 - React hooks rules
- **eslint-plugin-react-refresh** ^0.4.24 - Fast refresh support

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Performance

### Optimizations
- Vite's fast HMR during development
- Code splitting with dynamic imports (if needed)
- Image lazy loading via browser native support
- Minimal bundle size with tree shaking

### Lighthouse Targets
- Performance: 90+
- Accessibility: 90+
- Best Practices: 90+
- SEO: 90+