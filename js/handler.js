/*
        Load json file for sigml available for easy searching
    */
    $("#speech_loader").hide();
    $('#loader').hide();

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

    function getParsedText(speech) {
        // console.log("$$ 1");

        var HttpClient = function() {
            this.get = function(aUrl, aCallback) {
                var anHttpRequest = new XMLHttpRequest();
                anHttpRequest.onreadystatechange = function() {
                    if (anHttpRequest.readyState == 4 && anHttpRequest.status == 200)
                        aCallback(anHttpRequest.responseText);
                }

                anHttpRequest.open( "GET", aUrl, false );
                anHttpRequest.send( null );
            }
        };
        var final_response = "";
        var client = new HttpClient();
        var error_occurred = false;
        
        // Note: This is a SYNCHRONOUS request (false parameter), so callback executes before return
        try {
            client.get('http://localhost:5001/parser' + '?speech=' + encodeURIComponent(speech), function(response) {
                if (!response || response.trim() === '') {
                    console.error('Empty response from server');
                    error_occurred = true;
                    return;
                }
                
                try {
                    console.log(response);
                    final_response = JSON.parse(response);
                    
                    // Check if there's an error
                    if (final_response.error) {
                        console.error('Server error:', final_response.error);
                        error_occurred = true;
                        return;
                    }
                    
                    // Log final ISL text to console (AFTER response is received)
                    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                    console.log("🎯 TRANSLATION RESULT:");
                    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                    console.log("📝 Original English:", speech);
                    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                    console.log("✅ FINAL ISL TEXT (used for avatar):", final_response['isl_text_string'] || '');
                    console.log("🔧 Pre-processed String:", final_response['pre_process_string'] || '');
                    console.log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
                    
                    // Also log in a more visible way with styled output
                    if (final_response['isl_text_string']) {
                        console.log("%c🎯 FINAL ISL TEXT FOR AVATAR: " + final_response['isl_text_string'], "color: #00ff00; font-size: 16px; font-weight: bold; background: #000; padding: 5px;");
                    }
                    
                    if (document.getElementById('isl')) {
                        document.getElementById('isl').innerHTML = final_response['isl_text_string'] || '';
                    }
                    if (document.getElementById('speech_')) {
                        document.getElementById('speech_').innerHTML = speech; 
                    }
                } catch (parseError) {
                    console.error('Error parsing JSON response:', parseError);
                    console.error('Response was:', response);
                    error_occurred = true;
                }
            });
        } catch (requestError) {
            console.error('Error making request:', requestError);
            error_occurred = true;
        }
        
        // Since request is synchronous, final_response is set by now
        if (error_occurred || !final_response || !final_response['pre_process_string']) {
            return "";
        }
        return final_response['pre_process_string'] || "";
    }
    activateTab("menu1-h", "menu1"); // activate first menu by default
    // Whisper ASR support (with fallback to Web Speech API)
    function startDictationWithWhisper() {
        $('#speech_recognizer').hide();
        $("#speech_loader").show();
        $('#loader').hide();
        console.log('Speech recognition started with Whisper...');

        // Check if MediaRecorder is available
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            console.warn('MediaRecorder not available, falling back to Web Speech API');
            startDictation();
            return;
        }

        // Get audio stream
        navigator.mediaDevices.getUserMedia({ audio: true })
            .then(function(stream) {
                const mediaRecorder = new MediaRecorder(stream);
                const audioChunks = [];

                mediaRecorder.ondataavailable = function(event) {
                    audioChunks.push(event.data);
                };

                mediaRecorder.onstop = function() {
                    const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                    
                    // Send to Whisper API
                    const formData = new FormData();
                    formData.append('audio', audioBlob, 'recording.wav');

                    fetch('http://localhost:5001/api/transcribe', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => response.json())
                    .then(data => {
                        $('#speech_recognizer').show();
                        $("#speech_loader").hide();
                        $('#loader').show();

                        if (data.success && data.text) {
                            console.log('Whisper transcription: ' + data.text);
                            let speech = data.text;
                            let parsedSpeech = getParsedText(speech);
                            // Only call clickme if we got valid parsed speech
                            if (parsedSpeech && parsedSpeech.trim()) {
                                clickme(parsedSpeech);
                            } else {
                                console.error('Failed to get parsed text from server');
                                // Fallback to Web Speech API
                                startDictation();
                            }
                        } else {
                            console.error('Whisper error:', data.error);
                            // Fallback to Web Speech API
                            startDictation();
                        }
                        $('#loader').hide();

                        // Stop all tracks
                        stream.getTracks().forEach(track => track.stop());
                    })
                    .catch(error => {
                        console.error('Whisper API error:', error);
                        $("#speech_loader").hide();
                        $('#speech_recognizer').show();
                        // Fallback to Web Speech API
                        startDictation();
                        stream.getTracks().forEach(track => track.stop());
                    });
                };

                // Start recording
                mediaRecorder.start();
                console.log('Recording started...');

                // Stop recording after 5 seconds (or user can stop manually)
                setTimeout(function() {
                    if (mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                        console.log('Recording stopped...');
                    }
                }, 5000);

                // Add stop button functionality
                window.stopRecording = function() {
                    if (mediaRecorder.state === 'recording') {
                        mediaRecorder.stop();
                        stream.getTracks().forEach(track => track.stop());
                    }
                };

            })
            .catch(function(error) {
                console.error('Error accessing microphone:', error);
                $("#speech_loader").hide();
                $('#speech_recognizer').show();
                // Fallback to Web Speech API
                startDictation();
            });
    }

    function startDictation() {
        $('#speech_recognizer').hide();
        $("#speech_loader").show();
        console.log('Speech recognition started with Web Speech API...');

        if (window.hasOwnProperty('webkitSpeechRecognition')) {

            let recognition = new webkitSpeechRecognition();

            recognition.continuous = false;
            recognition.interimResults = false;

            recognition.lang = "en-US";
            recognition.start();

            recognition.onresult = function(e) {
                // document.getElementById('transcript').value = e.results[0][0].transcript;
                $('#speech_recognizer').show();
                $("#speech_loader").hide();
                $('#loader').show();

                console.log('Speech: ' + e.results[0][0].transcript);

                let speech = e.results[0][0].transcript;

                let parsedSpeech = getParsedText(speech);

                clickme(parsedSpeech);

                $('#loader').hide();

                recognition.stop();
                
                console.log('Speech recognition stopped...');

            };

            recognition.onerror = function(e) {
                console.error('Speech recognition error:', e);
                recognition.stop();
                $("#speech_loader").hide();
                $('#speech_recognizer').show();
            }

        } else {
            console.warn('Web Speech API not available');
            $("#speech_loader").hide();
            $('#speech_recognizer').show();
        }
    }

    // Default: Try Whisper first, fallback to Web Speech API
    function startDictationDefault() {
        // Try Whisper first (more accurate)
        startDictationWithWhisper();
    }

    var recognition = new webkitSpeechRecognition();
    recognition.continuous     = true;
    recognition.interimResults = true;

    recognition.onstart = function() {
        console.log("Recognition started");
    };
    recognition.onresult = function(event){
        var text = event.results[0][0].transcript;
        console.log(text);

        if (text === "stop avatar") {
            recognition.stop();
        }

        document.getElementById('dom-target').value = text;
        // clickme();

    };
    recognition.onerror = function(e) {
        console.log("Error");
    };

    // recognition.onend = function() {
    //     console.log("Speech recognition ended");
    // };

    function startDictation2() {
        recognition.lang = 'en-IN'; // 'en-US' works too, as do many others
        recognition.start();
    }

    function clickme(speech) {

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

        // wordArray object contains the word and corresponding files to be played
        // call the startPlayer on it in syn manner
        totalWords = wordArray.length;
        i = 0;

        var int = setInterval(function () {
            if(i == totalWords) {
                if(playerAvailableToPlay) {
                    clearInterval(int);
                    finalHint = $("#inputText").val();
                    $("#textHint").html(finalHint);
                }
            } else {
                if(playerAvailableToPlay) {
                    playerAvailableToPlay = false;
                    startPlayer("SignFiles/" + wordArray[i].fileName);
                    $("#textHint").html(wordArray[i].word);
                    i++;
                }
            }
        }, 3000);


    }
