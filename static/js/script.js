var keyDownTime = null;
var shiftPressed=false;
var capsLockPressed=false;
var capsLockTriggered = false;

        function captureKeyDown(event) {
            var key = event.key;
            if (key !== "Backspace" && key !== "Enter") {
                keyDownTime = performance.now();
                if (key === "Shift") {
                    shiftPressed = true;
                } 
                else if (key === "CapsLock") {
                    capsLockPressed = !capsLockPressed;
                    capsLockTriggered = true;
                }
                console.log("Key Down time: " + keyDownTime);
            }
        }

        function captureKeyUp(event) {
            var key = event.key;


            if (key === "Backspace") {
                // Clear the timings
                $.post("/clear_timings")
                    .done(function(data) {
                        // Handle the response if needed
                    })
                    .fail(function() {
                        console.log("Error clearing timings");
                    });
            } else if (key !== "Enter") {
                var keyUpTime = performance.now();
                console.log("Key Up time: " + keyUpTime);
                var keyToCapture = key.toLowerCase();

                if ((capsLockPressed || capsLockTriggered) && key !== "capslock") {
                    keyToCapture = "Capslock." + keyToCapture;
                    capsLockTriggered = false;
                }
                else if(shiftPressed && key !== "shift"){
                    keyToCapture="Shift."+keyToCapture;
                    shiftPressed=false;
                }

                if (keyToCapture !== "Capslock.capslock" && keyToCapture !== "Shift.shift" && keyToCapture !== "shift") {
                    $.post("/capture_keystrokes", { keyUpTime: keyUpTime, keyDownTime: keyDownTime, key: keyToCapture})
                        .done(function(data) {
                                // Handle the response if needed
                        })
                        .fail(function() {
                            console.log("Error in capturing keystrokes");
                        });
                }

            }
        }

        
        function validatePassword() {
            var password = document.getElementById("password").value;
            var regex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8}$/;

            if (!regex.test(password)) {
                alert("Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character.");
                return false;
            }
            return true;
        }