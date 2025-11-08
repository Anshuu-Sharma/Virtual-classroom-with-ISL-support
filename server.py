from flask import Flask, request, send_file, Response, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
# from nltk.corpus import stopwords
from nltk.parse.stanford import StanfordParser
from nltk.stem import WordNetLemmatizer
from nltk.tree import *
import os
import json
from six.moves import urllib
import zipfile
import sys
import time
import ssl
import subprocess
import re
import logging
import tempfile
from werkzeug.utils import secure_filename

# Import Whisper ASR service
try:
    from services.asr_service import get_asr_service
    from services.audio_processor import AudioProcessor
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper services not available. Install whisper and torch to enable.")

# Import ML Translation service
try:
    from services.translation_service import get_translation_service, is_ml_model_available
    ML_TRANSLATION_AVAILABLE = True
except ImportError:
    ML_TRANSLATION_AVAILABLE = False
    logging.warning("ML translation service not available.")

# Import ISL Mapper service
try:
    from services.isl_mapper import get_isl_mapper
    ISL_MAPPER_AVAILABLE = True
except ImportError:
    ISL_MAPPER_AVAILABLE = False
    logging.warning("ISL mapper service not available.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["2000000 per day", "500000 per hour"],
    storage_uri="memory://"
)

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': str(error)}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500

@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({'error': 'Rate limit exceeded', 'message': str(e.description)}), 429

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
print(BASE_DIR)
# Download zip file from https://nlp.stanford.edu/software/stanford-parser-full-2015-04-20.zip and extract in stanford-parser-full-2015-04-20 folder in higher directory
os.environ['CLASSPATH'] = os.path.join(BASE_DIR, 'stanford-parser-full-2018-10-17')
os.environ['STANFORD_MODELS'] = os.path.join(BASE_DIR,
                                             'stanford-parser-full-2018-10-17/edu/stanford/nlp/models/lexparser/englishPCFG.ser.gz')
os.environ['NLTK_DATA'] = '/usr/local/share/nltk_data/'


def is_parser_jar_file_present():
    stanford_parser_zip_file_path = os.environ.get('CLASSPATH') + ".jar"
    return os.path.exists(stanford_parser_zip_file_path)


def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = min(int(count*block_size*100/total_size),100)
    sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds passed" %
                    (percent, progress_size / (1024 * 1024), speed, duration))
    sys.stdout.flush()


def download_parser_jar_file():
    stanford_parser_zip_file_path = os.environ.get('CLASSPATH') + ".jar"
    url = "https://nlp.stanford.edu/software/stanford-parser-full-2018-10-17.zip"
    urllib.request.urlretrieve(url, stanford_parser_zip_file_path, reporthook)

def extract_parser_jar_file():
    stanford_parser_zip_file_path = os.environ.get('CLASSPATH') + ".jar"
    try:
        with zipfile.ZipFile(stanford_parser_zip_file_path) as z:
            z.extractall(path=BASE_DIR)
    except Exception:
        os.remove(stanford_parser_zip_file_path)
        download_parser_jar_file()
        extract_parser_jar_file()


def extract_models_jar_file():
    stanford_models_zip_file_path = os.path.join(os.environ.get('CLASSPATH'), 'stanford-parser-3.9.2-models.jar')
    stanford_models_dir = os.environ.get('CLASSPATH')
    with zipfile.ZipFile(stanford_models_zip_file_path) as z:
        z.extractall(path=stanford_models_dir)


def download_required_packages():
    if not os.path.exists(os.environ.get('CLASSPATH')):
        if is_parser_jar_file_present():
           pass
        else:
            download_parser_jar_file()
        extract_parser_jar_file()

    if not os.path.exists(os.environ.get('STANFORD_MODELS')):
        extract_models_jar_file()


def filter_stop_words(words):
    # Expanded stop words list - common words that don't have signs
    stopwords_set = set([
        'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing',
        'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'can', 'cannot', 'this', 'that', 'these', 'those',
        'so', 'than', 'then',  # Added these
        'about', 'above', 'across', 'after', 'against', 'along', 'among',
        'around', 'at', 'before', 'behind', 'below', 'beneath', 'beside',
        'between', 'beyond', 'by', 'during', 'except', 'for', 'from',
        'in', 'inside', 'into', 'like', 'near', 'of', 'off', 'on',
        'onto', 'out', 'outside', 'over', 'past', 'since', 'through',
        'throughout', 'till', 'to', 'toward', 'under', 'underneath',
        'until', 'up', 'upon', 'with', 'within', 'without'
    ])
    # Remove punctuation and lowercase for comparison
    words = list(filter(lambda x: x.lower().strip().rstrip('.,!?;:') not in stopwords_set, words))
    return words


def lemmatize_tokens(token_list):
    """Lemmatize tokens with proper POS tagging for better accuracy"""
    lemmatizer = WordNetLemmatizer()
    lemmatized_words = []
    
    # Try to use POS tagging for better accuracy
    try:
        from nltk.corpus import wordnet
        from nltk.tag import pos_tag
        
        # Get POS tags for better lemmatization
        try:
            pos_tags = pos_tag(token_list)
            
            # Map NLTK POS tags to WordNet POS tags
            def get_wordnet_pos(nltk_tag):
                if nltk_tag.startswith('J'):
                    return wordnet.ADJ
                elif nltk_tag.startswith('V'):
                    return wordnet.VERB
                elif nltk_tag.startswith('N'):
                    return wordnet.NOUN
                elif nltk_tag.startswith('R'):
                    return wordnet.ADV
                else:
                    return wordnet.NOUN  # Default to noun
            
            for token, pos_tag_val in pos_tags:
                wordnet_pos = get_wordnet_pos(pos_tag_val)
                lemmatized = lemmatizer.lemmatize(token.lower(), wordnet_pos)
                lemmatized_words.append(lemmatized)
        except Exception as e:
            # If POS tagging fails, use simple lemmatization
            logger.warning(f"POS tagging failed: {e}, using simple lemmatization")
            for token in token_list:
                # Try verb first (most common), then noun
                lemmatized = lemmatizer.lemmatize(token.lower(), wordnet.VERB)
                if lemmatized == token.lower():
                    lemmatized = lemmatizer.lemmatize(token.lower(), wordnet.NOUN)
                lemmatized_words.append(lemmatized)
    except ImportError:
        # If wordnet or pos_tag not available, use simple lemmatization
        logger.warning("NLTK wordnet/pos_tag not available, using simple lemmatization")
        for token in token_list:
            lemmatized = lemmatizer.lemmatize(token.lower())
            lemmatized_words.append(lemmatized)
    except Exception as e:
        # Fallback to simple lemmatization
        logger.error(f"Lemmatization error: {e}, using simple fallback")
        for token in token_list:
            try:
                lemmatized = lemmatizer.lemmatize(token.lower())
                lemmatized_words.append(lemmatized)
            except:
                # If everything fails, just lowercase
                lemmatized_words.append(token.lower())
    
    return lemmatized_words


def _is_ml_translation_confident(tokens, original_text):
    """Heuristic confidence check for ML translation output"""
    if not tokens:
        return False

    cleaned_tokens = [t.strip().lower() for t in tokens if t and t.strip()]
    if not cleaned_tokens:
        return False

    # Penalize outputs dominated by a single repeated token
    if len(cleaned_tokens) > 1:
        unique_ratio = len(set(cleaned_tokens)) / len(cleaned_tokens)
        if unique_ratio < 0.5:
            return False

    # Reject if unknown placeholders leak through
    if any(tok in {'<unk>', 'unk', '<pad>'} for tok in cleaned_tokens):
        return False

    # Compare overlap with original words (ignoring punctuation)
    orig_words = [
        re.sub(r'[^\w]', '', w.lower())
        for w in original_text.split()
        if w and w.lower() not in {'<sos>', '<eos>'}
    ]
    orig_words = [w for w in orig_words if w]

    if orig_words:
        overlap = len(set(orig_words) & set(cleaned_tokens))
        if overlap / len(set(orig_words)) < 0.4:
            return False

    return True


def label_parse_subtrees(parent_tree):
    tree_traversal_flag = {}

    for sub_tree in parent_tree.subtrees():
        tree_traversal_flag[sub_tree.treeposition()] = 0
    return tree_traversal_flag


def handle_noun_clause(i, tree_traversal_flag, modified_parse_tree, sub_tree):
    # if clause is Noun clause and not traversed then insert them in new tree first
    if tree_traversal_flag[sub_tree.treeposition()] == 0 and tree_traversal_flag[sub_tree.parent().treeposition()] == 0:
        tree_traversal_flag[sub_tree.treeposition()] = 1
        modified_parse_tree.insert(i, sub_tree)
        i = i + 1
    return i, modified_parse_tree


def handle_verb_prop_clause(i, tree_traversal_flag, modified_parse_tree, sub_tree):
    # if clause is Verb clause or Proportion clause recursively check for Noun clause
    for child_sub_tree in sub_tree.subtrees():
        if child_sub_tree.label() == "NP" or child_sub_tree.label() == 'PRP':
            if tree_traversal_flag[child_sub_tree.treeposition()] == 0 and tree_traversal_flag[child_sub_tree.parent().treeposition()] == 0:
                tree_traversal_flag[child_sub_tree.treeposition()] = 1
                modified_parse_tree.insert(i, child_sub_tree)
                i = i + 1
    return i, modified_parse_tree


def modify_tree_structure(parent_tree):
    # Mark all subtrees position as 0
    tree_traversal_flag = label_parse_subtrees(parent_tree)
    # Initialize new parse tree
    modified_parse_tree = Tree('ROOT', [])
    i = 0
    for sub_tree in parent_tree.subtrees():
        if sub_tree.label() == "NP":
            i, modified_parse_tree = handle_noun_clause(i, tree_traversal_flag, modified_parse_tree, sub_tree)
        if sub_tree.label() == "VP" or sub_tree.label() == "PRP":
            i, modified_parse_tree = handle_verb_prop_clause(i, tree_traversal_flag, modified_parse_tree, sub_tree)

    # recursively check for omitted clauses to be inserted in tree
    for sub_tree in parent_tree.subtrees():
        for child_sub_tree in sub_tree.subtrees():
            if len(child_sub_tree.leaves()) == 1:  #check if subtree leads to some word
                if tree_traversal_flag[child_sub_tree.treeposition()] == 0 and tree_traversal_flag[child_sub_tree.parent().treeposition()] == 0:
                    tree_traversal_flag[child_sub_tree.treeposition()] = 1
                    modified_parse_tree.insert(i, child_sub_tree)
                    i = i + 1

    return modified_parse_tree


def check_java_available():
    """Check if Java is installed and available"""
    try:
        # Try to run java command
        result = subprocess.run(['java', '-version'], 
                              stderr=subprocess.PIPE, 
                              stdout=subprocess.PIPE, 
                              timeout=5)
        # On macOS, even if java exists, it might return error code
        # but we get output if Java is installed
        if result.returncode == 0 or (result.stderr and len(result.stderr) > 0):
            return True
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        # If we get OSError about "Unable to locate Java Runtime", Java is not properly installed
        return False

def convert_eng_to_isl(input_string):
    """
    Convert English to ISL using ML model (if available) or Stanford Parser (fallback)
    """
    # Try ML model first if available
    if ML_TRANSLATION_AVAILABLE:
        try:
            translation_service = get_translation_service()
            if translation_service._model_loaded and translation_service.use_ml_model:
                logger.info("Using ML translation model")
                isl_tokens = translation_service.translate_ml(input_string)
                if _is_ml_translation_confident(isl_tokens, input_string):
                    return isl_tokens
                logger.info("ML translation deemed low confidence, using Stanford Parser fallback")
        except Exception as e:
            logger.warning(f"ML translation failed: {e}, falling back to Stanford Parser")
    
    # Fallback to Stanford Parser (rule-based)
    logger.info("Using Stanford Parser (rule-based translation)")
    
    # Check if Java is available before proceeding
    if not check_java_available():
        # If Java is not available, return a simple tokenized version
        # This allows the app to work partially until Java is installed
        logger.warning("Java is not installed. Stanford Parser requires Java.")
        logger.warning("Please install Java (JDK 8 or later) to enable full parsing functionality.")
        # Return simple tokenized input as fallback
        return input_string.split()
    
    # get all required packages
    download_required_packages()

    if len(list(input_string.split(' '))) == 1:
        return list(input_string.split(' '))

    try:
        # Initializing stanford parser
        parser = StanfordParser()

        # Generates all possible parse trees sort by probability for the sentence
        possible_parse_tree_list = [tree for tree in parser.parse(input_string.split())]

        # Get most probable parse tree
        parse_tree = possible_parse_tree_list[0]
        logger.debug(f"Parse tree: {parse_tree}")

        # Convert into tree data structure
        parent_tree = ParentedTree.convert(parse_tree)

        modified_parse_tree = modify_tree_structure(parent_tree)

        parsed_sent = modified_parse_tree.leaves()
        return parsed_sent
    except OSError as e:
        # If Java fails, provide a fallback
        logger.error(f"Stanford Parser failed - {str(e)}")
        logger.warning("Falling back to simple tokenization. Please install Java to enable full parsing.")
        return input_string.split()


def pre_process(sentence):
    """
    Pre-process sentence: break words not in words.txt into letters
    This is for the avatar player which needs to spell out unknown words
    """
    words = list(sentence.split())
    try:
        f = open('words.txt', 'r')
        eligible_words = f.read()
        f.close()
    except:
        logger.warning("words.txt not found, all words will be kept as-is")
        return sentence
    
    final_string = ""

    for word in words:
        # Clean word (remove punctuation for checking)
        clean_word = word.lower().rstrip('.,!?;:')
        
        # Check if word or its clean version is in eligible words
        if word in eligible_words or clean_word in eligible_words:
            final_string += " " + word
        else:
            # Break into letters if not found
            for letter in word:
                if letter.isalnum():  # Only letters/numbers
                    final_string += " " + letter
    
    return final_string

@app.route('/api/transcribe', methods=['POST'])
@limiter.limit("10 per minute")
def transcribe_audio():
    """
    Whisper ASR endpoint for speech-to-text conversion
    Accepts audio file upload or base64 encoded audio
    """
    if not WHISPER_AVAILABLE:
        return json.dumps({
            'error': 'Whisper service not available',
            'fallback': 'Use Web Speech API in browser'
        }), 503, {'Content-Type': 'application/json'}
    
    try:
        # Check if audio file is uploaded
        if 'audio' in request.files:
            audio_file = request.files['audio']
            if audio_file.filename == '':
                return json.dumps({'error': 'No audio file provided'}), 400
            
            # Save uploaded file temporarily with proper extension
            filename = secure_filename(audio_file.filename)
            # Get content type to determine actual format
            content_type = audio_file.content_type or 'audio/webm'
            logger.info(f"Received audio file: {filename}, content-type: {content_type}")
            
            # Determine file extension from content type
            ext_map = {
                'audio/webm': '.webm',
                'audio/wav': '.wav',
                'audio/wave': '.wav',
                'audio/x-wav': '.wav',
                'audio/mpeg': '.mp3',
                'audio/mp3': '.mp3'
            }
            ext = ext_map.get(content_type, '.webm')  # Default to webm for browser recordings
            
            temp_path = os.path.join(tempfile.gettempdir(), f"whisper_audio_{int(time.time())}{ext}")
            audio_file.save(temp_path)
            
            try:
                # Check file was saved
                if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                    return json.dumps({'error': 'Failed to save audio file'}), 400
                
                logger.info(f"Saved audio to: {temp_path} ({os.path.getsize(temp_path)} bytes)")
                
                # Validate audio file (basic check)
                file_size = os.path.getsize(temp_path)
                if file_size == 0:
                    return json.dumps({'error': 'Audio file is empty'}), 400
                if file_size > 50 * 1024 * 1024:  # 50MB max
                    return json.dumps({'error': 'Audio file too large'}), 400
                
                # Try to transcribe with Whisper
                # Note: Whisper internally uses ffmpeg for some formats
                # If ffmpeg is not available, this will fail gracefully
                try:
                    asr_service = get_asr_service(model_size="base")
                    result = asr_service.transcribe(temp_path)
                    
                    return json.dumps({
                        'text': result['text'],
                        'language': result.get('language', 'en'),
                        'success': True
                    }), 200, {'Content-Type': 'application/json'}
                    
                except RuntimeError as e:
                    # FFmpeg-related error
                    error_msg = str(e)
                    logger.warning(f"Whisper transcription failed (likely ffmpeg issue): {error_msg}")
                    return json.dumps({
                        'error': 'Whisper requires ffmpeg for audio processing. Please install ffmpeg or use Web Speech API.',
                        'fallback': 'Use Web Speech API in browser',
                        'details': error_msg,
                        'success': False
                    }), 503, {'Content-Type': 'application/json'}
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete temp file: {e}")
        
        # Check for base64 encoded audio
        elif 'audio_data' in request.json:
            import base64
            audio_data = request.json['audio_data']
            # Decode base64
            audio_bytes = base64.b64decode(audio_data.split(',')[1] if ',' in audio_data else audio_data)
            
            # Transcribe
            asr_service = get_asr_service(model_size="base")
            result = asr_service.transcribe_bytes(audio_bytes)
            
            return json.dumps({
                'text': result['text'],
                'language': result.get('language', 'en'),
                'success': True
            }), 200, {'Content-Type': 'application/json'}
        
        else:
            return json.dumps({'error': 'No audio data provided'}), 400
            
    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return json.dumps({
            'error': f'Transcription failed: {str(e)}',
            'success': False
        }), 500, {'Content-Type': 'application/json'}


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    whisper_status = WHISPER_AVAILABLE
    if WHISPER_AVAILABLE:
        try:
            asr_service = get_asr_service()
            whisper_status = asr_service.is_available()
        except:
            whisper_status = False
    
    # Check ML translation model
    ml_translation_status = False
    if ML_TRANSLATION_AVAILABLE:
        try:
            ml_translation_status = is_ml_model_available()
        except:
            ml_translation_status = False
    
    return json.dumps({
        'status': 'healthy',
        'whisper_available': whisper_status,
        'ml_translation_available': ml_translation_status
    }), 200, {'Content-Type': 'application/json'}


@app.route('/api/annotations', methods=['POST'])
@limiter.limit("20 per minute")
def add_annotation():
    """Add translation pair annotation"""
    try:
        from ml_pipeline.data_collector import DataCollector
        
        data = request.get_json()
        collector = DataCollector()
        
        pair_id = collector.add_translation_pair(
            english_text=data.get('english_text'),
            isl_text=data.get('isl_text'),
            isl_gloss=data.get('isl_gloss'),
            sigml_file=data.get('sigml_file'),
            source='manual_annotation',
            verified=False
        )
        
        return json.dumps({
            'id': pair_id,
            'success': True
        }), 200, {'Content-Type': 'application/json'}
        
    except Exception as e:
        logger.error(f"Annotation error: {str(e)}")
        return json.dumps({
            'error': str(e),
            'success': False
        }), 500, {'Content-Type': 'application/json'}


@app.route('/api/feedback', methods=['POST'])
@limiter.limit("30 per minute")
def add_feedback():
    """Add user feedback on translation"""
    try:
        from ml_pipeline.data_collector import DataCollector
        
        data = request.get_json()
        collector = DataCollector()
        
        feedback_id = collector.add_feedback(
            translation_pair_id=data.get('translation_pair_id'),
            feedback_type=data.get('feedback_type', 'user_correction'),
            is_correct=data.get('is_correct', True),
            corrected_text=data.get('corrected_text'),
            comments=data.get('comments')
        )
        
        return json.dumps({
            'id': feedback_id,
            'success': True
        }), 200, {'Content-Type': 'application/json'}
        
    except Exception as e:
        logger.error(f"Feedback error: {str(e)}")
        return json.dumps({
            'error': str(e),
            'success': False
        }), 500, {'Content-Type': 'application/json'}


@app.route('/annotation-tool', methods=['GET'])
def annotation_tool():
    """Serve annotation tool HTML"""
    annotation_path = os.path.join(BASE_DIR, 'data_collection', 'annotation_tool.html')
    if os.path.exists(annotation_path):
        return send_file(annotation_path)
    return "Annotation tool not found", 404


@app.route('/api/evaluation/metrics', methods=['GET'])
def get_evaluation_metrics():
    """Get current evaluation metrics"""
    try:
        # Load latest metrics from file (if available)
        metrics_file = os.path.join(BASE_DIR, 'data', 'latest_metrics.json')
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
            return json.dumps(metrics), 200, {'Content-Type': 'application/json'}
        else:
            return json.dumps({
                'message': 'No metrics available yet. Run evaluation first.'
            }), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"Error loading metrics: {str(e)}")
        return json.dumps({'error': str(e)}), 500, {'Content-Type': 'application/json'}


@app.route('/evaluation-dashboard', methods=['GET'])
def evaluation_dashboard():
    """Serve evaluation dashboard HTML"""
    dashboard_path = os.path.join(BASE_DIR, 'evaluation', 'dashboard.html')
    if os.path.exists(dashboard_path):
        return send_file(dashboard_path)
    return "Evaluation dashboard not found", 404


@app.route('/api/system/health', methods=['GET'])
def system_health():
    """Get detailed system health metrics"""
    try:
        from monitoring.health_check import get_system_health, check_service_health
        
        system = get_system_health()
        services = check_service_health()
        
        return json.dumps({
            'system': system,
            'services': services,
            'timestamp': time.time()
        }), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return json.dumps({
            'error': str(e),
            'status': 'error'
        }), 500, {'Content-Type': 'application/json'}


@app.route('/parser', methods=['GET', 'POST'])
def parseit():
    try:
        if request.method == "POST":
            input_string = request.form.get('text', '')
        else:
            input_string = request.args.get('speech', '')
        
        if not input_string:
            return json.dumps({
                'error': 'No input text provided',
                'isl_text_string': '',
                'pre_process_string': ''
            }), 400, {'Content-Type': 'application/json'}

        # print("input_string: " + input_string)
        input_string = input_string.capitalize()
        # input_string = input_string.lower()
        
        try:
            isl_parsed_token_list = convert_eng_to_isl(input_string)
        except Exception as e:
            logger.error(f"Error in convert_eng_to_isl: {e}")
            # Fallback to simple tokenization
            isl_parsed_token_list = input_string.split()
        
        # print("isl_parsed_token_list: " + ' '.join(isl_parsed_token_list))

        # Remove stop words FIRST (before lemmatization to reduce work)
        try:
            filtered_tokens = filter_stop_words(isl_parsed_token_list)
            logger.info(f"After stop word removal: {filtered_tokens}")
        except Exception as e:
            logger.error(f"Error in filter_stop_words: {e}")
            import traceback
            logger.error(traceback.format_exc())
            filtered_tokens = isl_parsed_token_list

        # Lemmatize tokens (convert "learning" -> "learn", "students" -> "student")
        try:
            lemmatized_tokens = lemmatize_tokens(filtered_tokens)
            logger.info(f"After lemmatization: {lemmatized_tokens}")
        except Exception as e:
            logger.error(f"Error in lemmatize_tokens: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback: just lowercase tokens
            lemmatized_tokens = [t.lower() for t in filtered_tokens]

        # Map English tokens to ISL glosses (AFTER lemmatization)
        isl_glosses = lemmatized_tokens
        if ISL_MAPPER_AVAILABLE:
            try:
                isl_mapper = get_isl_mapper()
                isl_glosses = isl_mapper.map_tokens_to_isl(lemmatized_tokens)
                logger.info(f"Mapped tokens: {lemmatized_tokens} -> {isl_glosses}")
            except Exception as e:
                logger.warning(f"ISL mapping failed: {e}, using original tokens")
                import traceback
                logger.warning(traceback.format_exc())
                isl_glosses = lemmatized_tokens

        isl_text_string = ""

        for gloss in isl_glosses:
            isl_text_string += gloss
            isl_text_string += " "

        isl_text_string = isl_text_string.lower().strip()
        
        # Log final ISL text for debugging
        logger.info(f"🔤 Final ISL Text (after all processing): '{isl_text_string}'")
        logger.info(f"📝 Tokens used: {isl_glosses}")

        try:
            pre_processed = pre_process(isl_text_string)
        except Exception as e:
            logger.error(f"Error in pre_process: {e}")
            pre_processed = isl_text_string

        # Log final ISL text to server console as well
        logger.info("=" * 80)
        logger.info("🎯 FINAL TRANSLATION RESULT")
        logger.info("=" * 80)
        logger.info(f"📝 Original English: {input_string}")
        logger.info(f"✅ FINAL ISL TEXT (used for avatar): {isl_text_string}")
        logger.info(f"🔧 Pre-processed String: {pre_processed}")
        logger.info("=" * 80)
        
        data = {
            'isl_text_string': isl_text_string,
            'pre_process_string': pre_processed,
            'original_english': input_string  # Include original for reference
        }
        return json.dumps(data), 200, {'Content-Type': 'application/json'}
        
    except Exception as e:
        logger.error(f"Error in /parser endpoint: {e}")
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Full traceback: {error_trace}")
        # Return error response with details
        return json.dumps({
            'error': f'Parsing failed: {str(e)}',
            'error_details': error_trace.split('\n')[-3] if error_trace else str(e),
            'isl_text_string': '',
            'pre_process_string': ''
        }), 500, {'Content-Type': 'application/json'}


@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/ml-comparison')
def ml_comparison():
    """ML comparison dashboard"""
    return send_file('evaluation/ml_comparison_dashboard.html')

@app.route('/hamnosysData/<path:filename>', methods=['GET', 'POST'])
def serve_hamnosys(filename):
    """Serve cached AnimGen JSON frames (local fallback for animgen server)."""
    try:
        file_path = os.path.join(BASE_DIR, 'hamnosysData', filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                content = f.read()
            return Response(
                content,
                mimetype='application/json',
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST',
                    'Access-Control-Allow-Headers': 'Content-Type'
                }
            )
        else:
            return Response('File not found', status=404, mimetype='text/plain')
    except Exception as e:
        return Response(f'Error serving file: {str(e)}', status=500, mimetype='text/plain')

@app.route('/animgen', methods=['POST', 'GET', 'OPTIONS'])
def animgen_proxy():
    """Local AnimGen proxy: map uploaded SiGML to cached JSON frames.

    The client posts form-data with a file field named 'sigml'. We extract the
    gloss name from the SiGML content (e.g., <hns_sign gloss="hello">) and
    respond with the contents of hamnosysData/<gloss>.txt (JSON array).
    """
    try:
        # Handle CORS preflight quickly
        if request.method == 'OPTIONS':
            return Response('', status=204, headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            })

        gloss = None

        # Prefer uploaded file content
        if 'sigml' in request.files:
            data = request.files['sigml'].read()
            try:
                text = data.decode('utf-8', errors='ignore')
            except Exception:
                text = ''
            # Try to extract gloss="..." from SiGML or HamNoSys
            m = re.search(r'gloss\s*=\s*"([^"]+)"', text, re.IGNORECASE)
            if m:
                gloss = m.group(1).strip()
            else:
                # Try filename hint inside the content (fallback)
                mf = re.search(r'<sigml[^>]*>(.*?)</sigml>', text, re.IGNORECASE | re.DOTALL)
                if mf:
                    # Very naive fallback: look for words
                    m2 = re.search(r'<hns_sign[^>]*gloss\s*=\s*"([^"]+)"', mf.group(1), re.IGNORECASE)
                    if m2:
                        gloss = m2.group(1).strip()

        # As an additional fallback, allow query parameter ?word=hello
        if gloss is None:
            gloss = request.args.get('word', '').strip() or None

        if not gloss:
            # Nothing to serve -> empty result
            return Response('[]', status=200, mimetype='application/json', headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            })

        # Map to cached JSON in hamnosysData
        candidate_files = [
            os.path.join(BASE_DIR, 'hamnosysData', f'{gloss}.txt'),
            os.path.join(BASE_DIR, 'hamnosysData', f'{gloss.lower()}.txt'),
            os.path.join(BASE_DIR, 'hamnosysData', f'{gloss.capitalize()}.txt'),
        ]
        target = next((p for p in candidate_files if os.path.exists(p)), None)
        if not target:
            return Response('[]', status=200, mimetype='application/json', headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            })

        with open(target, 'rb') as f:
            content = f.read()
        return Response(content, mimetype='application/json', headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })

    except Exception as e:
        return Response(f'Error: {str(e)}', status=500, mimetype='text/plain')

@app.route('/SignFiles/<path:filename>', methods=['GET', 'POST'])
def serve_sigml(filename):
    """Serve SIGML files with support for both GET and POST requests"""
    try:
        file_path = os.path.join(BASE_DIR, 'SignFiles', filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                content = f.read()
            # Return with appropriate content type for XML/SIGML files
            return Response(
                content,
                mimetype='application/xml',
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST',
                    'Access-Control-Allow-Headers': 'Content-Type'
                }
            )
        else:
            return Response('File not found', status=404, mimetype='text/plain')
    except Exception as e:
        return Response(f'Error serving file: {str(e)}', status=500, mimetype='text/plain')

@app.route('/avatars/<path:filename>', methods=['GET', 'POST', 'HEAD'])
def serve_avatar(filename):
    """Serve avatar JAR files and other avatar assets"""
    try:
        file_path = os.path.join(BASE_DIR, 'avatars', filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                content = f.read()
            # Determine MIME type based on file extension
            mimetype = 'application/java-archive' if filename.endswith('.jar') else 'application/octet-stream'
            return Response(
                content,
                mimetype=mimetype,
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST, HEAD, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Content-Length': str(len(content))
                }
            )
        else:
            return Response('File not found', status=404, mimetype='text/plain')
    except Exception as e:
        return Response(f'Error serving file: {str(e)}', status=500, mimetype='text/plain')

@app.route('/cwa/cwacfg.json', methods=['GET', 'POST'])
def serve_cwacfg():
    """Serve the CWAC configuration file"""
    try:
        file_path = os.path.join(BASE_DIR, 'js', 'cwacfg.json')
        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                content = f.read()
            return Response(
                content,
                mimetype='application/json',
                headers={
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, POST',
                    'Access-Control-Allow-Headers': 'Content-Type'
                }
            )
        else:
            return Response('Config file not found', status=404, mimetype='text/plain')
    except Exception as e:
        return Response(f'Error serving config: {str(e)}', status=500, mimetype='text/plain')

@app.route('/cwa/shaders/<path:filename>', methods=['GET', 'POST'])
def serve_shader(filename):
    """Serve shader files."""
    try:
        shader_src = None
        
        if filename.endswith('qskin.frag'):
            # Enhanced fragment shader aligned with CWASA uniform names
            shader_src = """#ifdef GL_ES
precision mediump float;
#endif

varying vec3 Normal;
varying vec2 TexCoord0;

uniform sampler2D Texture;

void main() {
    vec3 lightDir = normalize(vec3(0.5, 0.7, 1.0));
    vec3 normal = normalize(Normal);
    float NdotL = max(dot(normal, lightDir), 0.2);

    vec4 texColor = texture2D(Texture, TexCoord0);
    vec3 finalColor = texColor.rgb * NdotL;

    gl_FragColor = vec4(finalColor, texColor.a);
}"""
            
        elif filename.endswith('qskin.vert'):
            # Extract vertex shader from allcsa.js
            allcsa_path = os.path.join(BASE_DIR, 'js', 'allcsa.js')
            if os.path.exists(allcsa_path):
                with open(allcsa_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Find the vertex shader embedded code
                start_marker = 'if (theURI === "http://vhg.cmp.uea.ac.uk/tech/jas/vhg2017/cwa/shaders/qskin.vert")'
                idx = content.find(start_marker)
                if idx != -1:
                    jj_start = content.find('var jj = `', idx)
                    if jj_start != -1:
                        jj_start += len('var jj = `')
                        jj_end = content.find('`', jj_start)
                        if jj_end != -1:
                            shader_src = content[jj_start:jj_end]

        if shader_src is None:
            return Response('Shader not found', status=404, mimetype='text/plain')

        return Response(shader_src, mimetype='text/plain', headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        })
    except Exception as e:
        return Response(f'Error: {str(e)}', status=500, mimetype='text/plain')

@app.route('/cwa/h2s.xsl', methods=['GET', 'POST'])
def serve_h2s_xsl():
    """Serve the h2s.xsl transform file - extract from allcsa.js"""
    try:
        # The XSL is embedded in allcsa.js. We'll extract it using regex
        allcsa_path = os.path.join(BASE_DIR, 'js', 'allcsa.js')
        if os.path.exists(allcsa_path):
            with open(allcsa_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Use regex to extract the XSL content from the template literal
            # Pattern: find the if statement, then extract the content between backticks
            pattern = r'if \(theURI === ["\']http://vhg\.cmp\.uea\.ac\.uk/tech/jas/vhg2017/cwa/h2s\.xsl["\']\)\{[^`]*var jj = `([^`]+)`'
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                xsl_content = match.group(1)
                return Response(
                    xsl_content,
                    mimetype='application/xml',
                    headers={
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Methods': 'GET, POST',
                        'Access-Control-Allow-Headers': 'Content-Type'
                    }
                )
        
        # Fallback: return a minimal valid XSL if extraction fails
        fallback_xsl = '''<xsl:transform version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml" omit-xml-declaration="yes" indent="yes" encoding="UTF-8"/>
<xsl:template match="/">
    <xsl:copy-of select="."/>
</xsl:template>
</xsl:transform>'''
        return Response(
            fallback_xsl,
            mimetype='application/xml',
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )
    except Exception as e:
        return Response(f'Error: {str(e)}', status=500, mimetype='text/plain')

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Audio-to-Sign-Language Converter Server')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5001, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-debug', dest='debug', action='store_false', help='Disable debug mode')
    parser.set_defaults(debug=True)
    
    args = parser.parse_args()
    
    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info(f"Debug mode: {args.debug}")
    
    app.run(host=args.host, port=args.port, debug=args.debug)
