const fileInput = document.querySelector(".file-input"),
filterOptions = document.querySelectorAll(".filter button"),
fliterName = document.querySelector(".filter-info .name"),
fliterValue = document.querySelector(".filter-info .value"),
fliterSlider = document.querySelector(".slider input"),
rotateOptions = document.querySelectorAll(".rotate button"),
previewImg = document.querySelector(".preview-img img"),
resetFilterBtn = document.querySelector(".reset-filter"),
chooseImgBtn = document.querySelector(".choose-img"),
saveImgBtn= document.querySelector(".save-img");

let brightness = 100, saturation = 100, inversion = 0, grayscale = 0;
let rotate = 0, flipHorizontal = 1, flipVertical = 1;

const applyfilters = () => {
    previewImg.style.transform = `rotate(${rotate}deg) scale(${flipHorizontal}, ${flipVertical})`; // Rotate the image
    previewImg.style.filter = `brightness(${brightness}%) saturate(${saturation}%) invert(${inversion}%) grayscale(${grayscale}%)`;
}

const loadImage = () => {
    let file = fileInput.files[0]; // Get the first file
    if (!file) return; // If no file is selected, return
    previewImg.src = URL.createObjectURL(file); // Create a URL for the file
    previewImg.addEventListener("load", () => {
        resetFilterBtn.click(); // Reset the filters
        document.querySelector(".container").classList.remove('disable');
        resetCanvas(); // Reset the canvas
        measureOutput1.textContent = 'Distance1: 0 px (0 cm)'; // Reset measurement output
        measureOutput2.textContent = 'Distance2: 0 px (0 cm)'; // Reset measurement output
        angleOutput.textContent = 'Angle: 0°'; // Reset angle output
    });
}

filterOptions.forEach(option => {
    option.addEventListener("click", () => {
        document.querySelector('.filter .active').classList.remove('active');
        option.classList.add('active');
        fliterName.innerText = option.innerText;

        if(option.id === "brightness") {
            fliterSlider.max = 200;
            fliterSlider.value = brightness;
            fliterValue.innerText = `${brightness}%`;
        } else if (option.id === "saturation") {
            fliterSlider.max = 200;
            fliterSlider.value = saturation;
            fliterValue.innerText = `${saturation}%`;
        } else if (option.id === "inversion") {
            fliterSlider.max = 100;
            fliterSlider.value = inversion;
            fliterValue.innerText = `${inversion}%`;
        } else if (option.id === "grayscale") {
            fliterSlider.max = 100;
            fliterSlider.value = grayscale;
            fliterValue.innerText = `${grayscale}%`;
        }
    });
});

const updateFilter = () => {
    fliterValue.innerText = `${fliterSlider.value}%`;
    const selectedFilter = document.querySelector(".filter .active"); // Get the active filter

    if(selectedFilter.id === "brightness") {
        brightness = fliterSlider.value;
    } else if (selectedFilter.id === "saturation") {
        saturation = fliterSlider.value;
    } else if (selectedFilter.id === "inversion") {
        inversion = fliterSlider.value;
    } else {
        grayscale = fliterSlider.value;
    }
    applyfilters();
}

rotateOptions.forEach(option => {
    option.addEventListener("click", () => { // Add click event listener to each rotate option
        if(option.id === "left") {
            rotate -= 90; // Rotate left
        } else if (option.id === "right") {
            rotate += 90; // Rotate right
        } else if (option.id === "horizontal") {
            // if flipHorizontal is 1, set it to -1, else set it to 1
            flipHorizontal = flipHorizontal === 1 ? -1 : 1; // Rotate 180 degrees
        } else {
            // if flipVertical is 1, set it to -1, else set it to 1
            flipVertical = flipVertical === 1 ? -1 : 1; // Rotate 180 degrees
        }
        applyfilters();
    });
});

const resetFilter = () => {
    // Reset all filters
    brightness = 100; saturation = 100; inversion = 0; grayscale = 0;
    rotate = 0; flipHorizontal = 1; flipVertical = 1;
    applyfilters();
}

const saveIamge = () => {
    const canvas = document.createElement("canvas"); // Create a canvas element
    const ctx = canvas.getContext("2d"); // Get the context of the canvas

    // Adjust canvas dimensions based on rotation
    if (rotate % 180 !== 0) {
        canvas.width = previewImg.naturalHeight;
        canvas.height = previewImg.naturalWidth;
    } else {
        canvas.width = previewImg.naturalWidth;
        canvas.height = previewImg.naturalHeight;
    }

    // Apply filters to the image
    ctx.filter = `brightness(${brightness}%) saturate(${saturation}%) invert(${inversion}%) grayscale(${grayscale}%)`;
    ctx.translate(canvas.width / 2, canvas.height / 2); // Translate the canvas
    if (rotate !== 0) {
        ctx.rotate(rotate * Math.PI / 180); // Rotate the canvas
    }
    ctx.scale(flipHorizontal, flipVertical); // Flip the image
    ctx.drawImage(previewImg, -previewImg.naturalWidth / 2, -previewImg.naturalHeight / 2, previewImg.naturalWidth, previewImg.naturalHeight); // Draw the image on the canvas

    const link = document.createElement("a"); // Create a link element
    const fileName = fileInput.files[0].name; // Get the file name from the URL
    link.download = fileName.replace('.', '_edited.'); // Set the download attribute of the link
    link.href = canvas.toDataURL(); // Set the href attribute of the link
    link.click(); // Click the link to download the image
}

fileInput.addEventListener("change", loadImage);
fliterSlider.addEventListener("input", updateFilter);
resetFilterBtn.addEventListener("click", resetFilter);
saveImgBtn.addEventListener("click", saveIamge);
chooseImgBtn.addEventListener("click", () => fileInput.click());

const canvas = document.getElementById('measurement-canvas');
const ctx = canvas.getContext('2d');
const measureToggle = document.getElementById('measure-toggle');
const measureOutput1 = document.getElementById('measure-output1');
const measureOutput2 = document.getElementById('measure-output2');
const angleOutput = document.getElementById('angle-output');
let measurementEnabled = false;
let points = [];

const resetCanvas = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height); // Clear the canvas
    points = []; // Reset points array
    measureOutput1.textContent = 'Distance1: 0 px (0 cm)'; // Reset measurement output
    measureOutput2.textContent = 'Distance2: 0 px (0 cm)'; // Reset measurement output
    angleOutput.textContent = 'Angle: 0°'; // Reset angle output
};

// Ensure the canvas is correctly positioned and sized when the image is loaded
previewImg.addEventListener('load', () => {
    canvas.width = previewImg.clientWidth;
    canvas.height = previewImg.clientHeight;
    canvas.style.top = `${previewImg.offsetTop}px`;
    canvas.style.left = `${previewImg.offsetLeft}px`;
    resetCanvas(); // Reset the canvas when the image is loaded
});

measureToggle.addEventListener('click', () => {
    measurementEnabled = !measurementEnabled;
    measureToggle.textContent = measurementEnabled ? 'Disable Measurement' : 'Enable Measurement';
    canvas.style.pointerEvents = measurementEnabled ? 'auto' : 'none';
    if (!measurementEnabled) {
        resetCanvas(); // Clear canvas when disabling measurement
    }
});

const pxToCm = (px) => {
    const dpi = 96; // Assuming 96 DPI (dots per inch)
    const cmPerInch = 2.54;
    return (px / dpi) * cmPerInch;
};

canvas.addEventListener('mousedown', (e) => {
    if (!measurementEnabled) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    points.push({ x, y });

    if (points.length === 2) {
        drawLine(points[0], points[1], 'red');
        const distancePx = calculateDistance(points[0], points[1]);
        const distanceCm = pxToCm(distancePx);
        measureOutput1.textContent = `Distance1: ${distancePx.toFixed(2)} px (${distanceCm.toFixed(2)} cm)`;
    } else if (points.length === 3) {
        drawLine(points[1], points[2], 'blue');
        const distancePx = calculateDistance(points[1], points[2]);
        const distanceCm = pxToCm(distancePx);
        measureOutput2.textContent = `Distance2: ${distancePx.toFixed(2)} px (${distanceCm.toFixed(2)} cm)`;
        const angle = calculateAngle(points[0], points[1], points[2]);
        angleOutput.textContent = `Angle: ${angle.toFixed(2)}°`;
        points = [];
    }
});

canvas.addEventListener('mousemove', (e) => {
    if (!measurementEnabled || points.length === 0) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    if (points.length === 1) {
        drawLine(points[0], { x, y }, 'red');
        const distancePx = calculateDistance(points[0], { x, y });
        const distanceCm = pxToCm(distancePx);
        measureOutput1.textContent = `Distance1: ${distancePx.toFixed(2)} px (${distanceCm.toFixed(2)} cm)`;
    } else if (points.length === 2) {
        drawLine(points[0], points[1], 'red');
        drawLine(points[1], { x, y }, 'blue');
        const distancePx = calculateDistance(points[1], { x, y });
        const distanceCm = pxToCm(distancePx);
        measureOutput2.textContent = `Distance2: ${distancePx.toFixed(2)} px (${distanceCm.toFixed(2)} cm)`;
        const angle = calculateAngle(points[0], points[1], { x, y });
        angleOutput.textContent = `Angle: ${angle.toFixed(2)}°`;
    }
});

function drawLine(p1, p2, color) {
    ctx.beginPath();
    ctx.moveTo(p1.x, p1.y);
    ctx.lineTo(p2.x, p2.y);
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.stroke();
}

function drawAngle(p1, p2, p3) {
    drawLine(p1, p2);
    drawLine(p2, p3);
}

function calculateDistance(p1, p2) {
    return Math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2);
}

function calculateAngle(p1, p2, p3) {
    // Vectors AB and BC
    const vectorAB = { x: p2.x - p1.x, y: p2.y - p1.y };
    const vectorBC = { x: p3.x - p2.x, y: p3.y - p2.y };

    // Dot product and magnitudes
    const dotProduct = vectorAB.x * vectorBC.x + vectorAB.y * vectorBC.y;
    const magnitudeAB = Math.sqrt(vectorAB.x ** 2 + vectorAB.y ** 2);
    const magnitudeBC = Math.sqrt(vectorBC.x ** 2 + vectorBC.y ** 2);

    // Calculate angle (degrees)
    if (magnitudeAB === 0 || magnitudeBC === 0) {
        return null; // Prevent division by zero
    }
    const cosineTheta = dotProduct / (magnitudeAB * magnitudeBC);
    const angleRadians = Math.acos(Math.max(-1, Math.min(1, cosineTheta))); // Clamp value to [-1, 1]
    let angleDegrees = angleRadians * (180 / Math.PI); // Convert to degrees

    // Determine the direction of the angle (clockwise or counterclockwise)
    const crossProduct = vectorAB.x * vectorBC.y - vectorAB.y * vectorBC.x;
    if (crossProduct < 0) {
        // If cross product is negative, the angle is clockwise (approaching the red line)
        angleDegrees = 180 - angleDegrees;
    } else {
        // If cross product is positive, the angle is counterclockwise (moving away from the red line)
        angleDegrees = 180 - angleDegrees;
    }

    return angleDegrees;
}