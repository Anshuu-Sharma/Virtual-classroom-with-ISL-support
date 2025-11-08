/*
        Load json file for sigml available for easy searching
    */
    // $.getJSON("js/sigmlFiles.json", function(json){
    //     sigmlList = json;
    // });
    // code for clear button in input box for words
    $("#btnClear").click(function() {
        $("#inputText").val("");
    });

    // code to check if avatar has been loaded or not and hide the loading sign
    var loadingTout = setInterval(function() {
        if(tuavatarLoaded) {
            $("#loading").hide();
            clearInterval(loadingTout);
            console.log("Avatar loaded successfully !");
        }
    }, 1000);


    // code to animate tabs

    alltabhead = ["menu1-h", "menu2-h", "menu3-h", "menu4-h"];
    alltabbody = ["menu1", "menu2", "menu3", "menu4"];

    function activateTab(tabheadid, tabbodyid)
    {
        for(x = 0; x < alltabhead.length; x++)
            $("#"+alltabhead[x]).css("background-color", "white");
        $("#"+tabheadid).css("background-color", "#d5d5d5");
        for(x = 0; x < alltabbody.length; x++)
            $("#"+alltabbody[x]).hide();
        $("#"+tabbodyid).show();
    }

    var isContinuousListening = false;
    var recognitionInstance = null;
    var usingWhisperFallback = false;
    var mediaRecorderInstance = null;
    var mediaStreamRef = null;
    var liveTranscriptContainer = document.getElementById('live_transcript');
    var islTranscriptContainer = document.getElementById('isl_transcript');
    var queueContainer = document.getElementById('isl_queue');
    var wordsTranscriptContainer = document.getElementById('words_transcript');
    var interimTranscriptElement = null;
    var lastRecognizedUtterance = "";
    var playbackQueue = [];
    var pendingProcessingCount = 0;
    var currentPlaybackItem = null;
    var statusLoaderElement = $('#status_loader');
    var statusLoaderText = $('#status_loader_text');
    var statusLoaderImage = $('#status_loader_image');
    var currentLoaderMode = null;
    var listeningLoaderActive = false;

    var loaderVisualStates = {
        listening: {
            text: 'Listening...',
            image: 'images/speechloader.gif',
            alt: 'Listening animation'
        },
        processing: {
            text: 'Processing...',
            image: 'images/loader.gif',
            alt: 'Processing animation'
        }
    };

    function setStatusLoaderMode(mode) {
        if (!statusLoaderElement.length) {
            return;
        }
        if (!mode) {
            statusLoaderElement.hide();
            currentLoaderMode = null;
            return;
        }

        var config = loaderVisualStates[mode] || loaderVisualStates.processing;

        if (statusLoaderImage.length) {
            if (statusLoaderImage.attr('src') !== config.image) {
                statusLoaderImage.attr('src', config.image);
            }
            statusLoaderImage.attr('alt', config.alt);
        }

        if (statusLoaderText.length) {
            statusLoaderText.text(config.text);
        }

        statusLoaderElement.show();
        currentLoaderMode = mode;
    }

    function refreshStatusLoader() {
        if (pendingProcessingCount > 0) {
            setStatusLoaderMode('processing');
        } else if (listeningLoaderActive) {
            setStatusLoaderMode('listening');
        } else {
            setStatusLoaderMode(null);
        }
    }

    refreshStatusLoader();

    function scrollToBottom(element) {
        if (!element) {
            return;
        }
        element.scrollTop = element.scrollHeight;
    }

    function clearInterimTranscript() {
        if (interimTranscriptElement && interimTranscriptElement.parentNode) {
            interimTranscriptElement.parentNode.removeChild(interimTranscriptElement);
        }
        interimTranscriptElement = null;
    }

    function setInterimTranscript(text) {
        if (!liveTranscriptContainer) {
            return;
        }
        if (text && text.trim()) {
            if (!interimTranscriptElement) {
                interimTranscriptElement = document.createElement('p');
                interimTranscriptElement.className = 'interim-transcript';
                liveTranscriptContainer.appendChild(interimTranscriptElement);
            }
            interimTranscriptElement.textContent = text.trim();
            scrollToBottom(liveTranscriptContainer);
        } else {
            clearInterimTranscript();
        }
    }

    function appendLiveTranscriptEntry(text) {
        if (!liveTranscriptContainer || !text) {
                    return;
        }
        var paragraph = document.createElement('p');
        paragraph.textContent = text;
        liveTranscriptContainer.appendChild(paragraph);
        scrollToBottom(liveTranscriptContainer);
    }

    function appendISLTranscriptEntry(text) {
        if (!islTranscriptContainer || !text) {
            return;
        }
        var paragraph = document.createElement('p');
        paragraph.textContent = text;
        islTranscriptContainer.appendChild(paragraph);
        scrollToBottom(islTranscriptContainer);
    }

    function clearWordsTimeline() {
        if (!wordsTranscriptContainer) {
            return;
        }
        wordsTranscriptContainer.innerHTML = '';
        wordsTranscriptContainer.classList.add('is-empty');
        var placeholder = document.createElement('p');
        placeholder.className = 'words-placeholder';
        placeholder.textContent = 'Words will appear here as the avatar signs.';
        wordsTranscriptContainer.appendChild(placeholder);
    }

    function renderWordsTimeline(words) {
        if (!wordsTranscriptContainer) {
            return;
        }

        wordsTranscriptContainer.innerHTML = '';

        if (!words || !words.length) {
            clearWordsTimeline();
            return;
        }

        wordsTranscriptContainer.classList.remove('is-empty');
        var fragment = document.createDocumentFragment();

        words.forEach(function(word, index) {
            var chip = document.createElement('span');
            chip.className = 'word-chip';
            chip.textContent = word;
            chip.setAttribute('data-index', index);
            fragment.appendChild(chip);
        });

        wordsTranscriptContainer.appendChild(fragment);
    }

    function highlightActiveWord(index) {
        if (!wordsTranscriptContainer) {
            return;
        }
        var chips = wordsTranscriptContainer.querySelectorAll('.word-chip');
        chips.forEach(function(chip, chipIndex) {
            var isActive = chipIndex === index;
            chip.classList.toggle('active', isActive);
            chip.setAttribute('aria-current', isActive ? 'true' : 'false');
        });
    }

    clearWordsTimeline();

    function renderQueue() {
        if (!queueContainer) {
                        return;
        }
        queueContainer.innerHTML = '';
        playbackQueue.slice(-50).forEach(function(item) {
            var paragraph = document.createElement('p');
            var displayText = item.original;
            if (item.islText || item.preProcessed) {
                displayText += ' → ' + (item.islText || item.preProcessed);
            }
            displayText += ' [' + (item.status || 'pending') + ']';
            paragraph.textContent = displayText;
            paragraph.classList.add('queue-item');

            var statusClass = (item.status || 'pending').toLowerCase();
            paragraph.classList.add(statusClass);

            if (item.status === 'playing') {
                paragraph.setAttribute('aria-live', 'polite');
            }
            queueContainer.appendChild(paragraph);
        });
        scrollToBottom(queueContainer);
    }

    function showProcessingSpinner(active) {
        if (active) {
            pendingProcessingCount += 1;
        } else {
            pendingProcessingCount = Math.max(0, pendingProcessingCount - 1);
        }

        refreshStatusLoader();

        if (pendingProcessingCount > 0) {
            setTranscriptStatus('Processing...', 'active');
        } else if (!isContinuousListening) {
            setTranscriptStatus('Idle', 'idle');
        }
    }

    function setTranscriptStatus(label, state) {
        var pill = $('#transcript_status');
        if (!pill.length) {
            return;
        }

        pill.text(label || 'Idle');
        pill.removeClass('status-idle status-active status-error');

        switch (state) {
            case 'active':
                pill.addClass('status-active');
                break;
            case 'error':
                pill.addClass('status-error');
                break;
            default:
                pill.addClass('status-idle');
        }
    }

    function deriveTranscriptState(message) {
        if (!message) {
            return 'idle';
        }

        var lowered = message.toLowerCase();
        if (lowered.indexOf('error') !== -1 || lowered.indexOf('unavailable') !== -1) {
            return 'error';
        }
        if (lowered.indexOf('listen') !== -1 || lowered.indexOf('processing') !== -1 || lowered.indexOf('prepar') !== -1) {
            return 'active';
        }
        return 'idle';
    }

    function updateListeningStatus(message) {
        var displayMessage = message || 'Idle';
        $('#listening_status').text(displayMessage);
        setTranscriptStatus(displayMessage, deriveTranscriptState(displayMessage));
    }

    function updateListeningControls(active) {
        if (active) {
            $('#start_listening').hide();
            $('#stop_listening').show();
        } else {
            $('#start_listening').show();
            $('#stop_listening').hide();
        }
        listeningLoaderActive = active;
        refreshStatusLoader();
    }

    function requestParsedSentence(speech) {
        return fetch('http://localhost:5001/parser?speech=' + encodeURIComponent(speech), {
            method: 'GET'
        })
        .then(function(response) {
            if (!response.ok) {
                throw new Error('Parser request failed with status ' + response.status);
            }
            return response.text();
        })
        .then(function(body) {
            if (!body || body.trim() === '') {
                throw new Error('Empty response from parser');
            }
            var parsed;
            try {
                parsed = JSON.parse(body);
            } catch (error) {
                console.error('Error parsing JSON response:', error);
                throw error;
            }
            if (parsed.error) {
                throw new Error(parsed.error);
            }
            return parsed;
        });
    }

    function triggerAvatarPlayback(item) {
        if (!item || !item.preProcessed) {
            return;
        }
        processPlaybackQueue();
    }

    function processPlaybackQueue() {
        if (currentPlaybackItem && currentPlaybackItem.status === 'playing') {
            return;
        }

        var nextItem = null;
        for (var idx = 0; idx < playbackQueue.length; idx++) {
            if (playbackQueue[idx].status === 'ready') {
                nextItem = playbackQueue[idx];
                break;
            }
        }

        if (!nextItem) {
            return;
        }

        currentPlaybackItem = nextItem;
        nextItem.status = 'playing';
        renderQueue();

        clickme(nextItem.preProcessed, function() {
            nextItem.status = 'played';
            renderQueue();
            currentPlaybackItem = null;
            processPlaybackQueue();
        });
    }

    function queueSentenceForProcessing(sentence) {
        if (!sentence || !sentence.trim()) {
            return;
        }
        var item = {
            id: Date.now() + Math.random(),
            original: sentence,
            preProcessed: '',
            islText: '',
            status: 'processing'
        };
        playbackQueue.push(item);
        renderQueue();

        showProcessingSpinner(true);
        requestParsedSentence(sentence)
            .then(function(parsed) {
                item.preProcessed = (parsed['pre_process_string'] || '').trim();
                item.islText = (parsed['isl_text_string'] || '').trim();

                console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
                console.log('🎯 TRANSLATION RESULT:');
                console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
                console.log('📝 Original English:', sentence);
                console.log('✅ FINAL ISL TEXT (used for avatar):', item.islText);
                console.log('🔧 Pre-processed String:', item.preProcessed);
                console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

                if (item.islText) {
                    console.log('%c🎯 FINAL ISL TEXT FOR AVATAR: ' + item.islText, 'color: #00ff00; font-size: 16px; font-weight: bold; background: #000; padding: 5px;');
                }

                if (item.islText || item.preProcessed) {
                    appendISLTranscriptEntry(item.islText || item.preProcessed);
                }

                if (item.preProcessed) {
                    item.status = 'ready';
                    renderQueue();
                    triggerAvatarPlayback(item);
                } else {
                    item.status = 'no-match';
                    renderQueue();
                }
            })
            .catch(function(error) {
                console.error('Failed to process sentence:', error);
                item.status = 'error';
                renderQueue();
            })
            .finally(function() {
                showProcessingSpinner(false);
            });
    }

    function handleRecognizedSentence(sentence) {
        var cleaned = (sentence || '').trim();
        if (!cleaned) {
            return;
        }
        if (cleaned === lastRecognizedUtterance) {
            return;
        }
        lastRecognizedUtterance = cleaned;
        clearInterimTranscript();
        appendLiveTranscriptEntry(cleaned);
        queueSentenceForProcessing(cleaned);
    }

    function ensureRecognitionInstance() {
        if (recognitionInstance || !window.hasOwnProperty('webkitSpeechRecognition')) {
            return;
        }
        recognitionInstance = new webkitSpeechRecognition();
        recognitionInstance.continuous = true;
        recognitionInstance.interimResults = true;
        recognitionInstance.lang = 'en-US';

        recognitionInstance.onstart = function() {
            updateListeningStatus('Listening...');
            refreshStatusLoader();
        };

        recognitionInstance.onerror = function(event) {
            console.error('Speech recognition error:', event);
            if (event.error === 'no-speech') {
                updateListeningStatus('No speech detected');
            }
        };

        recognitionInstance.onend = function() {
            if (isContinuousListening) {
                try {
                    recognitionInstance.start();
                } catch (restartError) {
                    console.warn('Unable to restart recognition, switching to Whisper fallback.', restartError);
                    startWhisperFallback();
                }
            } else {
                updateListeningStatus('Idle');
                updateListeningControls(false);
            }
        };

        recognitionInstance.onresult = function(event) {
            var interim = '';
            for (var i = event.resultIndex; i < event.results.length; i++) {
                var result = event.results[i];
                if (!result[0]) {
                    continue;
                }
                var transcript = result[0].transcript || '';
                if (result.isFinal) {
                    handleRecognizedSentence(transcript);
                } else {
                    interim += transcript + ' ';
                }
            }
            setInterimTranscript(interim.trim());
        };
    }

    function transcribeWithWhisper(blob) {
        if (!blob) {
            return Promise.resolve('');
        }
        var formData = new FormData();
        formData.append('audio', blob, 'recording.wav');
        return fetch('http://localhost:5001/api/transcribe', {
            method: 'POST',
            body: formData
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data && data.success && data.text) {
                return data.text;
            }
            var message = (data && data.error) ? data.error : 'Unknown Whisper error';
            throw new Error(message);
        });
    }

    function handleWhisperChunk(blob) {
        showProcessingSpinner(true);
        transcribeWithWhisper(blob)
            .then(function(text) {
                if (text) {
                    handleRecognizedSentence(text);
                }
            })
            .catch(function(error) {
                console.error('Whisper transcription error:', error);
            })
            .finally(function() {
                showProcessingSpinner(false);
            });
    }

    function startWhisperFallback() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.warn('Media devices API not available.');
            updateListeningStatus('Microphone unavailable');
            updateListeningControls(false);
            isContinuousListening = false;
            return;
        }

        usingWhisperFallback = true;
        updateListeningStatus('Listening (Whisper)...');

        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function(stream) {
                mediaStreamRef = stream;
                mediaRecorderInstance = new MediaRecorder(stream);

                mediaRecorderInstance.onstart = function() {
                    refreshStatusLoader();
                };

                mediaRecorderInstance.ondataavailable = function(event) {
                    if (!isContinuousListening) {
                        return;
                    }
                    if (event.data && event.data.size > 0) {
                        handleWhisperChunk(event.data);
                    }
                };

                mediaRecorderInstance.onerror = function(error) {
                    console.error('MediaRecorder error:', error);
                };

                mediaRecorderInstance.start(5000);
            })
            .catch(function(error) {
                console.error('Error accessing microphone for Whisper:', error);
                updateListeningStatus('Microphone error');
                updateListeningControls(false);
                isContinuousListening = false;
            });
    }

    function stopWhisperFallback() {
        if (mediaRecorderInstance) {
            try {
                mediaRecorderInstance.stop();
            } catch (error) {
                console.warn('Error stopping MediaRecorder:', error);
            }
            mediaRecorderInstance = null;
        }
        if (mediaStreamRef) {
            mediaStreamRef.getTracks().forEach(function(track) {
                track.stop();
            });
            mediaStreamRef = null;
        }
        refreshStatusLoader();
    }

    function startContinuousListening() {
        if (isContinuousListening) {
            return;
        }
        isContinuousListening = true;
        lastRecognizedUtterance = '';
        updateListeningControls(true);
        updateListeningStatus('Preparing microphone...');

        if (window.hasOwnProperty('webkitSpeechRecognition')) {
            usingWhisperFallback = false;
            ensureRecognitionInstance();
            try {
                recognitionInstance.start();
            } catch (error) {
                console.warn('Failed to start Web Speech API, falling back to Whisper.', error);
                startWhisperFallback();
            }
        } else {
            startWhisperFallback();
        }
    }

    function stopContinuousListening() {
        if (!isContinuousListening) {
            return;
        }
        isContinuousListening = false;
        updateListeningControls(false);
        updateListeningStatus('Idle');
        clearInterimTranscript();

        if (recognitionInstance) {
            try {
                recognitionInstance.stop();
            } catch (error) {
                console.warn('Error stopping recognition:', error);
            }
        }

        stopWhisperFallback();
    }

    window.startContinuousListening = startContinuousListening;
    window.stopContinuousListening = stopContinuousListening;

    activateTab("menu1-h", "menu1"); // activate first menu by default

    function clickme(speech, onComplete) {

        if (!speech || !speech.trim()) {
            if (typeof onComplete === 'function') {
                onComplete();
            }
            return;
        }

        inputText = speech;
        // read the language that has been set
        lang = "English"; // using english for default
        tokens = [];

        if(lang=="English") {

            // tokenize the english paragraph
            tokenString = tokenizeEnglish(inputText);
            tokens = tokenString.split(',');
            console.log("Got tokens");

        } else if(lang == "Hindi") {

            // tokenize the english paragraph
            tokenString = tokenizeHindi(inputText);
            tokens = tokenString.split(',');
            console.log("Got tokens");

        }

        // remove empty values from tokens
        for(x = 0; x < tokens.length; x++) {
            t = tokens[x];

            if(t == "")
                tokens.splice(x, 1);
        }

        console.log(tokens);

        // process tokens based on language settings
        // use the script to generate the sigml files available and if
        // word file is available use word file less speak as letter based
        // list of sigmlfile is available in sigmlArray.js


        for(x = 0; x < tokens.length; x++) {
            // process each token
            t = tokens[x];
            if(t == "EOL")
                continue;
            // convert token to lower case for seaching in the database
            // search for name and it will return filename if it will exists
            t = t.toLowerCase();
            t = t.replace('.',""); // remove the puntuation from the end
            tokens[x] = t;
        }

        console.log(tokens);

        // reset the wordArray and arrayCounter here
        wordArray = [];
        arrayCounter = 0;
        console.log("sigmllength : "+sigmlList.length);
        for(x = 0; x < tokens.length; x++)
        {
            wordfoundflag = false;
            t = tokens[x];
            for(y = 0; y < sigmlList.length; y++) {
                if(sigmlList[y].name == t) {
                    // console.log(sigmlList[y].sid);
                    wordArray[arrayCounter++] = new FinalText(t, sigmlList[y].fileName);
                    wordfoundflag = true;
                    break;
                }
            }

            // if word not found then add chars - starts here
            if(wordfoundflag == false) {
                wordlen = t.length;
                for(p = 0; p < wordlen; p++) {
                    q = t[p];
                    //q=q.toUpperCase();
                    for(k = 0; k < sigmlList.length; k++) {
                        if(sigmlList[k].name == q) {
                            wordArray[arrayCounter++] = new FinalText(q, sigmlList[k].fileName);
                            break;
                        }
                    }
                }
                max = 0,countit=0;

                for(k=0;k<sigmlList.length;k++)
                {
                    countit++;
                    if(sigmlList[k].sid>max)
                    { max = sigmlList[k].sid; }
                }
                console.log("maxi is : "+max);
                max = max + 1;
                if(t!="EOL"){
                    console.log("k is : "+k);
                    var obj = {"sid": max,"name": t,"fileName": t+".sigml"};

                    var newdata = JSON.stringify(sigmlList);
                    console.log(newdata);

                }
            }
            // if not word found part ends here
        }


        console.log(wordArray);
        console.log(wordArray.length);
        
        // Log final word array for signing
        console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
        console.log("✋ FINAL SIGNS TO DISPLAY:");
        console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
        console.log("Total signs:", wordArray.length);
        wordArray.forEach((item, index) => {
            console.log(`${index + 1}. "${item.word}" → ${item.fileName}`);
        });
        console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

        $("#debugger").html(JSON.stringify(wordArray));

        var playbackWords = wordArray
            .map(function(entry) {
                return entry && entry.word ? entry.word : '';
            })
            .filter(function(word) {
                return word && word.trim();
            });

        renderWordsTimeline(playbackWords);
        highlightActiveWord(-1);

        // wordArray object contains the word and corresponding files to be played
        // call the startPlayer on it in syn manner
        totalWords = wordArray.length;
        i = 0;

        if (totalWords === 0) {
            if (typeof onComplete === 'function') {
                onComplete();
            }
            return;
        }

        var int = setInterval(function () {
            if(i == totalWords) {
                if(playerAvailableToPlay) {
                    clearInterval(int);
                    finalHint = $("#inputText").val();
                    $("#textHint").html(finalHint);
                    if (typeof onComplete === 'function') {
                        onComplete();
                    }
                }
            } else {
                if(playerAvailableToPlay) {
                    playerAvailableToPlay = false;
                    highlightActiveWord(i);
                    startPlayer("SignFiles/" + wordArray[i].fileName);
                    $("#textHint").html(wordArray[i].word);
                    i++;
                }
            }
        }, 3000);


    }
