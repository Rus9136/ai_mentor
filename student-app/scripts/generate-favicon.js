/**
 * Generate favicon.ico and apple-icon.png from icon.svg
 * Run: node scripts/generate-favicon.js
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const APP_DIR = path.join(__dirname, '..', 'src', 'app');
const SVG_PATH = path.join(APP_DIR, 'icon.svg');

async function generateFavicons() {
  console.log('Reading SVG from:', SVG_PATH);

  const svgBuffer = fs.readFileSync(SVG_PATH);

  // Generate apple-icon.png (180x180)
  console.log('Generating apple-icon.png (180x180)...');
  await sharp(svgBuffer)
    .resize(180, 180)
    .png()
    .toFile(path.join(APP_DIR, 'apple-icon.png'));
  console.log('Created apple-icon.png');

  // Generate PNG sizes for favicon
  console.log('Generating favicon sizes...');

  const size16 = await sharp(svgBuffer)
    .resize(16, 16)
    .png()
    .toBuffer();

  const size32 = await sharp(svgBuffer)
    .resize(32, 32)
    .png()
    .toBuffer();

  const size48 = await sharp(svgBuffer)
    .resize(48, 48)
    .png()
    .toBuffer();

  // For Next.js App Router, icon.png is the main favicon
  await sharp(svgBuffer)
    .resize(32, 32)
    .png()
    .toFile(path.join(APP_DIR, 'icon.png'));
  console.log('Created icon.png (32x32)');

  // Also create icon.png for various sizes
  await sharp(svgBuffer)
    .resize(192, 192)
    .png()
    .toFile(path.join(APP_DIR, 'icon-192.png'));
  console.log('Created icon-192.png');

  await sharp(svgBuffer)
    .resize(512, 512)
    .png()
    .toFile(path.join(APP_DIR, 'icon-512.png'));
  console.log('Created icon-512.png');

  console.log('\nDone! Files created in src/app/');
  console.log('Next.js will automatically use these files as favicon and icons.');
}

generateFavicons().catch(console.error);
