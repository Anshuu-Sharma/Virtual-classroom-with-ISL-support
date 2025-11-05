from flask import Flask, request, send_file, Response
from flask_cors import CORS
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

ssl._create_default_https_context = ssl._create_unverified_context

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.urandom(24)
CORS(app, supports_credentials=True)

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
    stopwords_set = set(['a', 'an', 'the', 'is'])
    # stopwords_set = set(stopwords.words("english"))
    words = list(filter(lambda x: x not in stopwords_set, words))
    return words


def lemmatize_tokens(token_list):
    lemmatizer = WordNetLemmatizer()
    lemmatized_words = []
    for token in token_list:
        lemmatized_words.append(lemmatizer.lemmatize(token))

    return lemmatized_words


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
    # Check if Java is available before proceeding
    if not check_java_available():
        # If Java is not available, return a simple tokenized version
        # This allows the app to work partially until Java is installed
        print("WARNING: Java is not installed. Stanford Parser requires Java.")
        print("Please install Java (JDK 8 or later) to enable full parsing functionality.")
        print("On macOS, you can install it with: brew install openjdk")
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
        print(parse_tree)
        # output = '(ROOT
        #               (S
        #                   (PP (IN As) (NP (DT an) (NN accountant)))
        #                   (NP (PRP I))
        #                   (VP (VBP want) (S (VP (TO to) (VP (VB make) (NP (DT a) (NN payment))))))
        #                )
        #             )'

        # Convert into tree data structure
        parent_tree = ParentedTree.convert(parse_tree)

        modified_parse_tree = modify_tree_structure(parent_tree)

        parsed_sent = modified_parse_tree.leaves()
        return parsed_sent
    except OSError as e:
        # If Java fails, provide a fallback
        print(f"ERROR: Stanford Parser failed - {str(e)}")
        print("Falling back to simple tokenization. Please install Java to enable full parsing.")
        return input_string.split()


def pre_process(sentence):
    words = list(sentence.split())
    f = open('words.txt', 'r')
    eligible_words = f.read()
    f.close()
    final_string = ""

    for word in words:
        if word not in eligible_words:
            for letter in word:
                final_string += " " + letter
        else:
            final_string += " " + word

    return final_string

@app.route('/parser', methods=['GET', 'POST'])
def parseit():
    if request.method == "POST":
        input_string = request.form['text']
    else:
        input_string = request.args.get('speech')

    # print("input_string: " + input_string)
    input_string = input_string.capitalize()
    # input_string = input_string.lower()
    isl_parsed_token_list = convert_eng_to_isl(input_string)
    # print("isl_parsed_token_list: " + ' '.join(isl_parsed_token_list))

    # lemmatize tokens
    lemmatized_isl_token_list = lemmatize_tokens(isl_parsed_token_list)
    # print("lemmatized_isl_token_list: " + ' '.join(lemmatized_isl_token_list))

    # remove stop words
    filtered_isl_token_list = filter_stop_words(lemmatized_isl_token_list)
    # print("filtered_isl_token_list: " + ' '.join(filtered_isl_token_list))




    isl_text_string = ""

    for token in filtered_isl_token_list:
        isl_text_string += token
        isl_text_string += " "

    isl_text_string = isl_text_string.lower()

    data = {
        'isl_text_string': isl_text_string,
        'pre_process_string': pre_process(isl_text_string)
    }
    return json.dumps(data)


@app.route('/')
def index():
    return app.send_static_file('index.html')

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
            # Enhanced fragment shader with texture and lighting support
            shader_src = """#ifdef GL_ES
precision mediump float;
#endif

varying vec3 Normal;
varying vec2 TexCoord0;

uniform sampler2D MainTexture;
uniform bool UseTexture;

void main() {
    vec3 lightDir = normalize(vec3(0.5, 0.7, 1.0));
    vec3 normal = normalize(Normal);
    float NdotL = max(dot(normal, lightDir), 0.2);
    
    vec4 texColor = vec4(0.9, 0.8, 0.7, 1.0); // Default skin tone
    
    if (UseTexture) {
        texColor = texture2D(MainTexture, TexCoord0);
    }
    
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
    app.run(host="0.0.0.0", port=5001, debug=True)
