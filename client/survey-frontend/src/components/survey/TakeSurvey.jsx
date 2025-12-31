import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { publicAPI } from '../../api/axios';
import { useAuth } from '../../contexts/AuthContext';
import { Send, CheckCircle, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const TakeSurvey = () => {
  const { surveyId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [survey, setSurvey] = useState(null);
  const [answers, setAnswers] = useState({});
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [isOwnSurvey, setIsOwnSurvey] = useState(false);

  useEffect(() => {
    fetchSurvey();
  }, [surveyId]);

  const fetchSurvey = async () => {
    try {
      const response = await publicAPI.getSurvey(surveyId);
      const surveyData = response.data;
      setSurvey(surveyData);
      
      // Check if user is trying to answer their own survey
      if (user && surveyData.created_by === user.id) {
        setIsOwnSurvey(true);
      }
    } catch (error) {
      toast.error('Survey not found or unavailable');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerChange = (questionId, value) => {
    setAnswers({
      ...answers,
      [questionId]: value
    });
  };

  const handleCheckboxChange = (questionId, option) => {
    const currentAnswers = answers[questionId] || [];
    let newAnswers;
    
    if (currentAnswers.includes(option)) {
      newAnswers = currentAnswers.filter(item => item !== option);
    } else {
      newAnswers = [...currentAnswers, option];
    }
    
    setAnswers({
      ...answers,
      [questionId]: newAnswers
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate all questions are answered
    for (const question of survey.questions) {
      if (!answers[question.id] || 
          (Array.isArray(answers[question.id]) && answers[question.id].length === 0)) {
        toast.error('Please answer all questions');
        return;
      }
    }

    setSubmitting(true);

    try {
      await publicAPI.submitResponse(surveyId, { answers });
      setSubmitted(true);
      toast.success('Thank you for your response!');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Failed to submit response');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading survey...</p>
      </div>
    );
  }

  if (submitted) {
    return (
      <div className="success-container">
        <div className="success-card">
          <CheckCircle size={64} color="#10b981" />
          <h1>Thank You!</h1>
          <p>Your response has been recorded successfully.</p>
          <button onClick={() => navigate('/dashboard')} className="btn btn-primary">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  if (!survey) {
    return <div className="error-message">Survey not found</div>;
  }

  // Prevent survey creator from answering their own survey
  if (isOwnSurvey) {
    return (
      <div className="restriction-container">
        <div className="restriction-card">
          <AlertCircle size={64} color="#f59e0b" />
          <h1>Cannot Answer Your Own Survey</h1>
          <p>You created this survey, so you cannot submit a response to it.</p>
          <p className="share-hint">Share the survey link with others to collect responses:</p>
          <div className="share-link-box">
            <input 
              type="text" 
              value={window.location.href} 
              readOnly 
              className="share-link-input"
            />
            <button 
              onClick={() => {
                navigator.clipboard.writeText(window.location.href);
                toast.success('Link copied to clipboard!');
              }}
              className="btn btn-primary"
            >
              Copy Link
            </button>
          </div>
          <button onClick={() => navigate('/dashboard')} className="btn btn-outline">
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="take-survey-container">
      <div className="survey-header">
        <h1>{survey.title}</h1>
        {survey.description && <p className="survey-description">{survey.description}</p>}
      </div>

      <form onSubmit={handleSubmit} className="survey-questions">
        {survey.questions.map((question, index) => (
          <div key={question.id} className="question-block">
            <div className="question-header">
              <span className="question-number">Question {index + 1}</span>
              <span className="required-badge">Required</span>
            </div>
            <h3 className="question-text">{question.text}</h3>

            {question.type === 'text' && (
              <textarea
                value={answers[question.id] || ''}
                onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                placeholder="Type your answer here..."
                rows={4}
                required
              />
            )}

            {question.type === 'radio' && (
              <div className="options-list">
                {question.options.map((option, optIndex) => (
                  <label key={optIndex} className="radio-option">
                    <input
                      type="radio"
                      name={question.id}
                      value={option}
                      checked={answers[question.id] === option}
                      onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                      required
                    />
                    <span>{option}</span>
                  </label>
                ))}
              </div>
            )}

            {question.type === 'checkbox' && (
              <div className="options-list">
                {question.options.map((option, optIndex) => (
                  <label key={optIndex} className="checkbox-option">
                    <input
                      type="checkbox"
                      checked={(answers[question.id] || []).includes(option)}
                      onChange={() => handleCheckboxChange(question.id, option)}
                    />
                    <span>{option}</span>
                  </label>
                ))}
              </div>
            )}

            {question.type === 'select' && (
              <select
                value={answers[question.id] || ''}
                onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                required
              >
                <option value="">-- Select an option --</option>
                {question.options.map((option, optIndex) => (
                  <option key={optIndex} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            )}

            {question.type === 'rating' && (
              <div className="rating-options">
                {[1, 2, 3, 4, 5].map((rating) => (
                  <label key={rating} className="rating-option">
                    <input
                      type="radio"
                      name={question.id}
                      value={rating}
                      checked={answers[question.id] === rating.toString()}
                      onChange={(e) => handleAnswerChange(question.id, e.target.value)}
                      required
                    />
                    <span className="rating-number">{rating}</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        ))}

        <button type="submit" className="btn btn-primary btn-lg" disabled={submitting}>
          <Send size={20} />
          {submitting ? 'Submitting...' : 'Submit Response'}
        </button>
      </form>
    </div>
  );
};

export default TakeSurvey;