import { useState } from 'react';
import './GameSetup.css';

function GameSetup({ onStart, loading }) {
  const [difficulty, setDifficulty] = useState('short');
  const [topN, setTopN] = useState(200);

  const handleSubmit = (e) => {
    e.preventDefault();
    onStart(difficulty, topN);
  };

  return (
    <div className="game-setup">
      <h2>Start New Game</h2>
      
      <form onSubmit={handleSubmit} className="setup-form">
        <div className="form-group">
          <label htmlFor="difficulty">Career Length:</label>
          <select
            id="difficulty"
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            disabled={loading}
          >
            <option value="short">Short (2-4 clubs)</option>
            <option value="moderate">Moderate (5-7 clubs)</option>
            <option value="long">Long (8+ clubs)</option>
          </select>
          <small>Longer careers are harder to guess</small>
        </div>

        <div className="form-group">
          <label htmlFor="topN">Player Pool:</label>
          <select
            id="topN"
            value={topN}
            onChange={(e) => setTopN(Number(e.target.value))}
            disabled={loading}
          >
            <option value="50">Top 50 (Easier - Superstars)</option>
            <option value="100">Top 100 (Easy)</option>
            <option value="200">Top 200 (Medium)</option>
            <option value="500">Top 500 (Hard)</option>
            <option value="1000">Top 1000 (Very Hard)</option>
          </select>
          <small>Smaller pool = more famous players</small>
        </div>

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
        >
          {loading ? 'Starting...' : 'Start Game'}
        </button>
      </form>

      <div className="game-info">
        <h3>How to Play:</h3>
        <ol>
          <li>You'll see a sequence of club logos</li>
          <li>Guess which player had this career path</li>
          <li>Type the player's name and submit</li>
          <li>Get points for correct guesses!</li>
        </ol>
      </div>
    </div>
  );
}

export default GameSetup;