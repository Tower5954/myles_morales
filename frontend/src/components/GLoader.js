// components/GLoader.js
import React, { useRef, useEffect } from 'react';
import './GLoader.css'; // Create this CSS file for additional styling

const GLoader = ({ size = 500, color = '#26A6AB', backgroundColor = '#f0f0f0', speed = 100 }) => {
  const svgRef = useRef(null);
  const raysRef = useRef([]);
  const animationRef = useRef(null);
  
  useEffect(() => {
    if (!svgRef.current) return;
    
    // Clear any existing content
    while (svgRef.current.firstChild) {
      svgRef.current.removeChild(svgRef.current.firstChild);
    }
    
    // Reset rays array
    raysRef.current = [];
    
    // Set up dimensions - match the HTML version's proportions more closely
    const centerX = size / 2;
    const centerY = size / 2;
    const centerRadius = size * (40/500); // Exactly 40px when size is 500
    
    // Draw the center circle as the bottom layer
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.setAttribute('cx', centerX);
    circle.setAttribute('cy', centerY);
    circle.setAttribute('r', centerRadius);
    circle.setAttribute('fill', 'transparent');
    svgRef.current.appendChild(circle);
    
    // Create a tapered ray
    const createTaperedRay = (startX, startY, endX, endY, startWidth, endWidth) => {
      // Calculate the angle of the ray
      const dx = endX - startX;
      const dy = endY - startY;
      const angle = Math.atan2(dy, dx);
      
      // Calculate perpendicular points for the start (base)
      const startTopX = startX + (startWidth / 2) * Math.sin(angle);
      const startTopY = startY - (startWidth / 2) * Math.cos(angle);
      const startBottomX = startX - (startWidth / 2) * Math.sin(angle);
      const startBottomY = startY + (startWidth / 2) * Math.cos(angle);
      
      // Calculate perpendicular points for the end (tip)
      const endTopX = endX + (endWidth / 2) * Math.sin(angle);
      const endTopY = endY - (endWidth / 2) * Math.cos(angle);
      const endBottomX = endX - (endWidth / 2) * Math.sin(angle);
      const endBottomY = endY + (endWidth / 2) * Math.cos(angle);
      
      // Create a path with a flat base and rounded tip
      const pathData = `
          M ${startTopX} ${startTopY} 
          L ${endTopX} ${endTopY} 
          A ${endWidth/2} ${endWidth/2} 0 1 1 ${endBottomX} ${endBottomY}
          L ${startBottomX} ${startBottomY} 
          Z
      `;
      
      // Create the path element
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', pathData);
      path.setAttribute('fill', color);
      
      return path;
    };
    
    // Total number of rays (including the horizontal ray)
    const totalRays = 19;
    
    // Create the horizontal ray (special case) - starts at center
    // Match exactly the HTML values (180px when size is 500)
    const horizontalRayLength = size * (180/500);
    const horizontalRay = createTaperedRay(
      centerX, centerY,                      // Start at center
      centerX + horizontalRayLength, centerY, // End point
      size * (10/500), size * (18/500)       // Match original proportions exactly
    );
    svgRef.current.appendChild(horizontalRay);
    raysRef.current.push(horizontalRay);
    
    // Ray angles distribution - same as HTML
    const startAngle = 15;  // Start after horizontal ray
    const endAngle = 270;   // End at 12 o'clock position
    
    // First ray after horizontal should be short
    let isShortRay = true;
    
    // Distribute rays around part of the circle
    for (let i = 0; i < totalRays - 1; i++) {
      // Distribute rays evenly
      const angle = startAngle + (i / (totalRays - 2)) * (endAngle - startAngle);
      const radians = angle * Math.PI / 180;
      
      // Calculate ray start point - moved OUTSIDE the circle by 5px (proportional)
      const startDistance = centerRadius + size * (5/500);
      const startX = centerX + (startDistance * Math.cos(radians));
      const startY = centerY + (startDistance * Math.sin(radians));
      
      // Calculate length - match HTML values exactly (110px long rays when size is 500)
      const longRayLength = size * (110/500);
      const shortRayLength = longRayLength * 0.75;
      const length = isShortRay ? shortRayLength : longRayLength;
      
      // End point
      const endX = centerX + ((startDistance + length) * Math.cos(radians));
      const endY = centerY + ((startDistance + length) * Math.sin(radians));
      
      // Width - match HTML values exactly
      const baseWidth = size * (6/500);
      const tipWidth = isShortRay ? size * (12/500) : size * (16/500);
      
      // Create ray
      const ray = createTaperedRay(startX, startY, endX, endY, baseWidth, tipWidth);
      svgRef.current.appendChild(ray);
      raysRef.current.push(ray);
      
      // Toggle between short and long rays
      isShortRay = !isShortRay;
    }
    
    // Set up the ticking animation
    let currentActiveRay = 0;
    let lastTick = 0;
    
    function animate(timestamp) {
      if (!lastTick || timestamp - lastTick >= speed) {
        // Reset all rays to default color
        raysRef.current.forEach(ray => ray.setAttribute('fill', color));
        
        // Set active ray to white
        raysRef.current[currentActiveRay].setAttribute('fill', 'white');
        
        // Move to next ray
        currentActiveRay = (currentActiveRay + 1) % raysRef.current.length;
        
        // Update last tick time
        lastTick = timestamp;
      }
      
      // Continue animation loop
      animationRef.current = requestAnimationFrame(animate);
    }
    
    // Start animation
    animationRef.current = requestAnimationFrame(animate);
    
    // Cleanup function
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [size, color, backgroundColor, speed]); // Re-run when these props change
  
  return (
    <div className="g-loader-container" style={{ 
      position: 'relative', 
      width: size, 
      height: size,
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center'
    }}>
      <svg 
        ref={svgRef} 
        width={size} 
        height={size} 
        viewBox={`0 0 ${size} ${size}`}
        style={{ display: 'block' }} // Prevent extra space below SVG
      />
    </div>
  );
};

export default GLoader;