import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import h5Api, { getH5Token } from '@/lib/h5Api';

const STAR_LABELS = ['非常差', '较差', '一般', '满意', '非常满意'];

/**
 * H5 评价页
 * URL: /h5/:customerId/orders/:orderId/review
 */
export function H5ReviewPage() {
  const { customerId, orderId } = useParams<{ customerId: string; orderId: string }>();
  const navigate = useNavigate();
  const [rating, setRating] = useState(0);
  const [hovered, setHovered] = useState(0);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async () => {
    if (rating === 0) {
      setError('请先评分');
      return;
    }
    setSubmitting(true);
    setError('');
    try {
      await h5Api.post(`/${customerId}/orders/${orderId}/review`, {
        rating,
        comment: comment.trim(),
      });
      setDone(true);
    } catch (e: unknown) {
      const msg = (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail || '提交失败';
      setError(msg);
    } finally {
      setSubmitting(false);
    }
  };

  if (done) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="text-center max-w-sm">
          <div className="text-6xl mb-4">🎉</div>
          <h2 className="text-xl font-bold text-gray-900">评价成功！</h2>
          <p className="text-gray-500 mt-2">感谢您的反馈，我们会继续努力提供更好的服务。</p>
          <Link
            to={`/h5/${customerId}/orders`}
            className="inline-block mt-6 bg-blue-600 text-white px-6 py-3 rounded-xl font-medium"
          >
            返回订单列表
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <button onClick={() => navigate(-1)} className="text-blue-600 text-xl">←</button>
        <h1 className="text-lg font-bold text-gray-900">评价服务</h1>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm">
        {/* Stars */}
        <div className="text-center mb-6">
          <p className="text-sm text-gray-500 mb-3">请为本次服务评分</p>
          <div className="flex justify-center gap-2">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                onClick={() => setRating(star)}
                onMouseEnter={() => setHovered(star)}
                onMouseLeave={() => setHovered(0)}
                className="text-4xl transition-transform hover:scale-110"
              >
                {star <= (hovered || rating) ? '⭐' : '☆'}
              </button>
            ))}
          </div>
          {rating > 0 && (
            <p className="text-sm text-blue-600 mt-2 font-medium">
              {STAR_LABELS[rating - 1]}
            </p>
          )}
        </div>

        {/* Comment */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-600 mb-2">留言（选填）</label>
          <textarea
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            rows={4}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            placeholder="说说您的服务体验..."
          />
        </div>

        {error && (
          <div className="bg-red-50 text-red-600 rounded-lg p-3 text-sm mb-4">{error}</div>
        )}

        <button
          onClick={handleSubmit}
          disabled={submitting || rating === 0}
          className="w-full bg-orange-500 text-white py-3 rounded-xl font-medium hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {submitting ? '提交中...' : '提交评价'}
        </button>
      </div>
    </div>
  );
}
