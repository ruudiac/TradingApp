import os
import base64
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from chart_analyzer import ChartAnalyzer
from models import Trade, SessionLocal, init_db

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
app.config['UPLOAD_FOLDER'] = 'uploads'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

init_db()

analyzer = ChartAnalyzer()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    return render_template('history.html')

@app.route('/analyze', methods=['POST'])
def analyze_chart():
    if 'chart' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['chart']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Please upload PNG, JPG, JPEG, GIF, or WebP'}), 400
    
    try:
        image_data = file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        mime_type = file.content_type or 'image/png'
        
        analysis_result = analyzer.analyze_chart(image_data, mime_type)
        
        if analysis_result.get('error'):
            return jsonify({
                'success': False,
                'error': analysis_result.get('message', 'Analysis failed'),
                'analysis': analysis_result
            }), 500
        
        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'image_preview': f'data:{mime_type};base64,{image_base64}'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/trades', methods=['GET'])
def get_trades():
    db = SessionLocal()
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        indicator_type = request.args.get('indicator_type')
        outcome = request.args.get('outcome')
        
        query = db.query(Trade)
        
        if start_date:
            query = query.filter(Trade.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            end = datetime.fromisoformat(end_date) + timedelta(days=1)
            query = query.filter(Trade.created_at < end)
        if indicator_type and indicator_type != 'all':
            query = query.filter(Trade.indicator_type == indicator_type)
        if outcome and outcome != 'all':
            query = query.filter(Trade.outcome == outcome)
        
        trades = query.order_by(Trade.created_at.desc()).all()
        
        return jsonify({
            'success': True,
            'trades': [{
                'id': t.id,
                'created_at': t.created_at.isoformat() if t.created_at else None,
                'symbol': t.symbol,
                'recommendation': t.recommendation,
                'confidence_level': t.confidence_level,
                'trend_direction': t.trend_direction,
                'outcome': t.outcome,
                'profit_loss': t.profit_loss,
                'indicator_type': t.indicator_type,
                'rsi_signal': t.rsi_signal,
                'macd_signal': t.macd_signal,
                'entry_price': t.entry_price,
                'exit_price': t.exit_price,
                'notes': t.notes
            } for t in trades]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/trades', methods=['POST'])
def save_trade():
    db = SessionLocal()
    try:
        data = request.json
        
        trade = Trade(
            symbol=data.get('symbol'),
            recommendation=data.get('recommendation', 'HOLD'),
            confidence_level=data.get('confidence_level'),
            trend_direction=data.get('trend_direction'),
            outcome=data.get('outcome'),
            profit_loss=data.get('profit_loss'),
            indicator_type=data.get('indicator_type'),
            rsi_signal=data.get('rsi_signal'),
            macd_signal=data.get('macd_signal'),
            entry_price=data.get('entry_price'),
            exit_price=data.get('exit_price'),
            notes=data.get('notes'),
            raw_analysis=data.get('raw_analysis')
        )
        
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        return jsonify({
            'success': True,
            'trade_id': trade.id
        })
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/trades/<int:trade_id>', methods=['PUT'])
def update_trade(trade_id):
    db = SessionLocal()
    try:
        data = request.json
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        
        if not trade:
            return jsonify({'success': False, 'error': 'Trade not found'}), 404
        
        if 'outcome' in data:
            trade.outcome = data['outcome']
        if 'profit_loss' in data:
            trade.profit_loss = data['profit_loss']
        if 'exit_price' in data:
            trade.exit_price = data['exit_price']
        if 'notes' in data:
            trade.notes = data['notes']
        
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/trades/<int:trade_id>', methods=['DELETE'])
def delete_trade(trade_id):
    db = SessionLocal()
    try:
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        
        if not trade:
            return jsonify({'success': False, 'error': 'Trade not found'}), 404
        
        db.delete(trade)
        db.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@app.route('/api/stats', methods=['GET'])
def get_stats():
    db = SessionLocal()
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        indicator_type = request.args.get('indicator_type')
        
        query = db.query(Trade)
        
        if start_date:
            query = query.filter(Trade.created_at >= datetime.fromisoformat(start_date))
        if end_date:
            end = datetime.fromisoformat(end_date) + timedelta(days=1)
            query = query.filter(Trade.created_at < end)
        if indicator_type and indicator_type != 'all':
            query = query.filter(Trade.indicator_type == indicator_type)
        
        trades = query.all()
        
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.outcome == 'win')
        losing_trades = sum(1 for t in trades if t.outcome == 'loss')
        pending_trades = sum(1 for t in trades if t.outcome is None or t.outcome == 'pending')
        
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_profit_loss = sum(t.profit_loss or 0 for t in trades)
        
        performance_by_date = {}
        for trade in trades:
            if trade.created_at:
                date_key = trade.created_at.strftime('%Y-%m-%d')
                if date_key not in performance_by_date:
                    performance_by_date[date_key] = {'wins': 0, 'losses': 0, 'pending': 0, 'profit_loss': 0}
                if trade.outcome == 'win':
                    performance_by_date[date_key]['wins'] += 1
                elif trade.outcome == 'loss':
                    performance_by_date[date_key]['losses'] += 1
                else:
                    performance_by_date[date_key]['pending'] += 1
                performance_by_date[date_key]['profit_loss'] += trade.profit_loss or 0
        
        performance_by_indicator = {}
        for trade in trades:
            ind = trade.indicator_type or 'Unknown'
            if ind not in performance_by_indicator:
                performance_by_indicator[ind] = {'wins': 0, 'losses': 0, 'total': 0}
            performance_by_indicator[ind]['total'] += 1
            if trade.outcome == 'win':
                performance_by_indicator[ind]['wins'] += 1
            elif trade.outcome == 'loss':
                performance_by_indicator[ind]['losses'] += 1
        
        return jsonify({
            'success': True,
            'stats': {
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'pending_trades': pending_trades,
                'win_rate': round(win_rate, 2),
                'total_profit_loss': round(total_profit_loss, 2),
                'performance_by_date': performance_by_date,
                'performance_by_indicator': performance_by_indicator
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        db.close()

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
