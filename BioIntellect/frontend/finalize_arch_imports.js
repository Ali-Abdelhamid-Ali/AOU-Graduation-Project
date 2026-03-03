import fs from 'fs';
import path from 'path';

const SRC_DIR = 'src';

const IMPORT_CORRECTIONS = {
    // API Group
    '@/services/api/endpoints': '@/services/api',
    '@/services/api/axios.config': '@/services/api',
    '@/services/apiClient': '@/services/api',

    // Other Services
    '@/services/medicalService': '@/services/medical.service',
    '@/services/mriSegmentationService': '@/services/clinical.service',
    '@/services/notificationService': '@/services/notification.service',

    // Utils
    '@/utils/formatters': '@/utils/formatters', // already folder
    '@/utils/validation': '@/utils/validators',
    '@/utils/securityUtils': '@/utils/helpers/security',
    '@/utils/verificationUtils': '@/utils/helpers/verification',
};

function walk(dir) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        if (fs.statSync(fullPath).isDirectory()) {
            walk(fullPath);
        } else if (/\.(js|jsx|ts|tsx)$/.test(file)) {
            fixImports(fullPath);
        }
    }
}

function fixImports(filePath) {
    let content = fs.readFileSync(filePath, 'utf8');
    let originalContent = content;

    // Sorted by length descending
    const sortedCorrections = Object.entries(IMPORT_CORRECTIONS).sort((a, b) => b[0].length - a[0].length);

    for (const [oldImport, newImport] of sortedCorrections) {
        // Match: import ... from 'OLD_IMPORT' or import ... from "OLD_IMPORT"
        // Also handle possible trailing slash
        const regex = new RegExp(`(['"])${oldImport}(\\/)?(['"])`, 'g');
        content = content.replace(regex, `$1${newImport}$3`);
    }

    if (content !== originalContent) {
        fs.writeFileSync(filePath, content, 'utf8');
        console.log(`Final Arch Fix: ${filePath}`);
    }
}

console.log('Finalizing architecture imports...');
walk(SRC_DIR);
console.log('Architecture normalization complete!');
