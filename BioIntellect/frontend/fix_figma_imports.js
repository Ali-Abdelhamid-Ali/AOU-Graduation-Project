import fs from 'fs';
import path from 'path';

const SRC_DIR = 'src';

function walk(dir) {
    if (!fs.existsSync(dir)) return;
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        if (fs.statSync(fullPath).isDirectory()) {
            walk(fullPath);
        } else if (/\.(js|jsx|ts|tsx|css)$/.test(file)) {
            if (fullPath.includes('FIGMA')) {
                fixFigmaImports(fullPath);
            }
        }
    }
}

function fixFigmaImports(filePath) {
    let content = fs.readFileSync(filePath, 'utf8');
    let originalContent = content;

    // Normalizing separators for matching
    const normalizedPath = filePath.split(path.sep).join('/');

    // Fix @/ imports
    content = content.replace(/['"]@\/components\/ui\/([^'"]+)['"]/g, (match, p1) => {
        if (normalizedPath.includes('PAGE/FIGMA')) return `'../../UI/FIGMA/${p1}'`;
        if (normalizedPath.includes('UI/FIGMA')) return `'./${p1}'`;
        if (normalizedPath.includes('LAYOUT/FIGMA')) return `'../../UI/FIGMA/${p1}'`;
        return match;
    });

    content = content.replace(/['"]@\/lib\/utils['"]/g, (match) => {
        if (normalizedPath.includes('UI/FIGMA')) return `'../../UTILS/FIGMA/utils'`;
        return match;
    });

    // Fix relative imports from original structure
    if (normalizedPath.includes('PAGE/FIGMA')) {
        content = content.replace(/['"]\.\.\/components\/ui\/([^'"]+)['"]/g, "'../../UI/FIGMA/$1'");
        content = content.replace(/['"]\.\.\/components\/([^'"]+)['"]/g, (match, p1) => {
            if (p1.endsWith('.css')) return match;
            return `'../../LAYOUT/FIGMA/${p1}'`;
        });
    }

    if (normalizedPath.includes('LAYOUT/FIGMA')) {
        content = content.replace(/['"]\.\/ui\/([^'"]+)['"]/g, "'../../UI/FIGMA/$1'");
        content = content.replace(/['"]\.\.\/components\/ui\/([^'"]+)['"]/g, "'../../UI/FIGMA/$1'");
        content = content.replace(/['"]\.\.\/components\/([^'"]+)['"]/g, (match, p1) => {
            if (p1.endsWith('.css')) return match;
            return `'../../LAYOUT/FIGMA/${p1}'`;
        });
    }

    if (normalizedPath.includes('UI/FIGMA')) {
        content = content.replace(/['"]\.\/utils['"]/g, "'../../UTILS/FIGMA/utils'");
    }

    // Common dependency fixes
    content = content.replace(/['"]motion\/react['"]/g, "'framer-motion'");

    if (content !== originalContent) {
        fs.writeFileSync(filePath, content, 'utf8');
        console.log(`Updated Figma file: ${filePath}`);
    }
}

walk(SRC_DIR);
console.log('Finished fixing Figma imports!');
