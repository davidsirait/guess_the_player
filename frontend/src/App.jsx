import { useState } from 'react';
import { sessionAPI } from './services/api';
import GameSetup from './components/GameSetup';
import GamePlay from './components/GamePlay';
import GameResult from './components/GameResult';
import './App.css';

function App() {
  // Game states
  const [gameState, setGameState] = useState('setup'); // 'setup', 'playing', 'result'
  const [sessionId, setSessionId] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [score, setScore] = useState(0);
  const [totalAttempts, setTotalAttempts] = useState(0);
  const [lastGuessResult, setLastGuessResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Settings
  const [difficulty, setDifficulty] = useState('short');
  const [topN, setTopN] = useState(200);

  // Start new game
  const handleStartGame = async (selectedDifficulty, selectedTopN) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await sessionAPI.startSession(selectedDifficulty, selectedTopN);
      
      setSessionId(data.session_id);
      setCurrentQuestion(data.question);
      setScore(data.score);
      setTotalAttempts(data.total_attempts);
      setDifficulty(selectedDifficulty);
      setTopN(selectedTopN);
      setGameState('playing');
    } catch (err) {
      setError('Failed to start game: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Submit guess
  const handleGuess = async (guess) => {
    if (!guess.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const result = await sessionAPI.submitGuess(sessionId, guess);
      
      setScore(result.session_score);
      setTotalAttempts(result.total_attempts);
      setLastGuessResult(result);
      
      // If correct, show result screen
      if (result.correct) {
        setGameState('result');
      }
    } catch (err) {
      setError('Failed to submit guess: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // Get next question (with optional difficulty/topN change)
  const handleNextQuestion = async (newDifficulty = null, newTopN = null) => {
    setLoading(true);
    setError(null);
    setLastGuessResult(null);
    
    try {
      const data = await sessionAPI.getNextQuestion(sessionId, newDifficulty, newTopN);
      
      setCurrentQuestion(data.question);
      setScore(data.session_score);
      setTotalAttempts(data.total_attempts);
      
      // Update stored difficulty/topN if changed
      if (newDifficulty) setDifficulty(newDifficulty);
      if (newTopN) setTopN(newTopN);
      
      setGameState('playing');
    } catch (err) {
      setError('Failed to get next question: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  // End game
  const handleEndGame = async () => {
    if (!sessionId) {
      setGameState('setup');
      return;
    }
    
    setLoading(true);
    
    try {
      await sessionAPI.endSession(sessionId);
      
      // Reset everything
      setSessionId(null);
      setCurrentQuestion(null);
      setScore(0);
      setTotalAttempts(0);
      setLastGuessResult(null);
      setGameState('setup');
    } catch (err) {
      console.error('Failed to end session:', err);
      // Still reset UI even if API fails
      setGameState('setup');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>⚽ Guess the Player</h1>
        {gameState !== 'setup' && (
          <div className="score-display">
            <span>Score: {score}/{totalAttempts}</span>
          </div>
        )}
      </header>

      <main className="app-main">
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        {gameState === 'setup' && (
          <GameSetup 
            onStart={handleStartGame}
            loading={loading}
          />
        )}

        {gameState === 'playing' && currentQuestion && (
          <GamePlay
            question={currentQuestion}
            onGuess={handleGuess}
            lastGuessResult={lastGuessResult}
            loading={loading}
            onEndGame={handleEndGame}
          />
        )}

        {gameState === 'result' && lastGuessResult && (
          <GameResult
            result={lastGuessResult}
            score={score}
            totalAttempts={totalAttempts}
            currentDifficulty={difficulty}
            currentTopN={topN}
            onNextQuestion={handleNextQuestion}
            onEndGame={handleEndGame}
            loading={loading}
          />
        )}
      </main>

      {<footer className="app-footer">
        <p>Powered by Transfermarkt data</p>
      </footer> }
    </div>
  );
}

export default App;