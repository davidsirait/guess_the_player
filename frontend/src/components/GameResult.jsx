import { useState } from 'react';
import './GameResult.css';

function GameResult({ result, score, totalAttempts, currentDifficulty, currentTopN, onNextQuestion, onEndGame, loading }) {
  
  // State for next question settings
  const [nextDifficulty, setNextDifficulty] = useState(currentDifficulty);
  const [nextTopN, setNextTopN] = useState(currentTopN);
  
  // Handle image error - fallback to placeholder
  const handleImageError = (e) => {
    e.target.src = '/static/images/placeholders/default-player.png';
  };

  // Calculate accuracy
  const accuracy = totalAttempts > 0 ? (score / totalAttempts * 100).toFixed(1) : 0;

  // Handle next question with potential difficulty change
  const handleNext = () => {
    // Only pass parameters if they changed from current values
    const diffToPass = nextDifficulty !== currentDifficulty ? nextDifficulty : null;
    const topNToPass = nextTopN !== currentTopN ? nextTopN : null;
    
    onNextQuestion(diffToPass, topNToPass);
  };

  return (
    <div className="game-result">
      <div className="result-header">
        <h2>✅ Correct!</h2>
        <p className="congrats">You guessed it right!</p>
      </div>

      {/* Main player reveal */}
      <div className="player-reveal">
        <div className="player-image-main">
          <img
            src={result.actual_answer_img_url}
            alt={result.actual_answer}
            onError={handleImageError}
          />
        </div>
        <h3 className="player-name">{result.actual_answer}</h3>
      </div>

      {/* Other possible answers (if multiple players share the path) */}
      {result.all_possible_answers.length > 1 && (
        <div className="other-answers">
          <p className="other-answers-title">
            Other players with the same path:
          </p>
          <div className="other-answers-grid">
            {result.all_possible_answers.map((player, index) => {
              // Skip the main answer
              if (player === result.actual_answer) return null;
              
              return (
                <div key={index} className="other-player">
                  <img
                    src={result.all_possible_answers_img_urls[index]}
                    alt={player}
                    onError={handleImageError}
                  />
                  <p>{player}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Score display */}
      <div className="score-summary">
        <h3>Your Stats</h3>
        <div className="stats-grid">
          <div className="stat-item">
            <span className="stat-value">{score}</span>
            <span className="stat-label">Correct</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{totalAttempts}</span>
            <span className="stat-label">Total Attempts</span>
          </div>
          <div className="stat-item">
            <span className="stat-value">{accuracy}%</span>
            <span className="stat-label">Accuracy</span>
          </div>
        </div>
      </div>

      {/* Action buttons */}
      <div className="result-actions">
        <button
          onClick={onNextQuestion}
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? 'Loading...' : 'Next Question'}
        </button>
        <button
          onClick={onEndGame}
          className="btn btn-secondary"
          disabled={loading}
        >
          End Game
        </button>
      </div>
    </div>
  );
}

export default GameResult;