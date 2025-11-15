import { useState } from 'react';
import './GamePlay.css';

function GamePlay({ question, onGuess, lastGuessResult, loading, onEndGame }) {
  const [guess, setGuess] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (guess.trim()) {
      onGuess(guess);
      setGuess(''); // Clear input after submitting
    }
  };

  // Handle image error - fallback to placeholder
  const handleImageError = (e) => {
    e.target.src = '/static/images/placeholders/default-club.png';
  };

  return (
    <div className="game-play">
      <div className="question-header">
        <h2>Guess the Player</h2>
        <p className="difficulty-badge">{question.difficulty.toUpperCase()}</p>
      </div>

      {/* Club sequence display */}
      <div className="clubs-container">
        <h3>Career Path:</h3>
        <div className="clubs-grid">
          {question.clubs.map((club, index) => (
            <>
              <div key={index} className="club-item">
                <div className="club-logo">
                  <img
                    src={club.logo}
                    alt={club.club}
                    onError={handleImageError}
                  />
                </div>
                <div className="club-info">
                  <p className="club-name">{club.club}</p>
                  <p className="club-season">{club.season}</p>
                </div>
              </div>
              {index < question.clubs.length - 1 && (
                <div key={`arrow-${index}`} className="arrow">→</div>
              )}
            </>
          ))}
        </div>
      </div>

      {/* Guess input */}
      <div className="guess-section">
        <form onSubmit={handleSubmit} className="guess-form">
          <input
            type="text"
            value={guess}
            onChange={(e) => setGuess(e.target.value)}
            placeholder="Enter player name..."
            className="guess-input"
            disabled={loading}
            autoFocus
          />
          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading || !guess.trim()}
          >
            {loading ? 'Checking...' : 'Submit Guess'}
          </button>
        </form>

        {/* Show feedback for wrong guesses */}
        {lastGuessResult && !lastGuessResult.correct && (
          <div className="guess-feedback wrong">
            <p>❌ Not quite! Try again.</p>
            <p className="similarity">
              Similarity: {lastGuessResult.similarity_score.toFixed(0)}%
            </p>
            {lastGuessResult.similarity_score > 70 && (
              <p className="hint">You're close!</p>
            )}
          </div>
        )}
      </div>

      {/* Additional info */}
      <div className="question-stats">
        <p>Number of clubs: {question.num_moves}</p>
        {question.shared_by > 1 && (
          <p className="hint">⚠️ {question.shared_by} players share this exact path!</p>
        )}
      </div>

      {/* End game button */}
      <button
        onClick={onEndGame}
        className="btn btn-secondary"
        disabled={loading}
      >
        End Game
      </button>
    </div>
  );
}

export default GamePlay;