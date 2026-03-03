import fs from 'fs';
import path from 'path';

const SRC_DIR = 'src_new';

const ALIAS_MAPPING = {
    // FEATURES
    'COMPONENTS/AUTH': '@/features/auth/components',
    'COMPONENTS/CLINICAL': '@/features/clinical/components',
    'COMPONENTS/DASHBOARD': '@/features/dashboard/components',
    'features/auth': '@/features/auth',
    'features/clinical': '@/features/clinical',
    'features/dashboard': '@/features/dashboard',

    // COMPONENTS
    'COMPONENTS/NAVIGATION': '@/components/layout',
    'COMPONENTS/ui': '@/components/ui',
    'COMPONENTS/layout': '@/components/layout',
    'components/ui': '@/components/ui',
    'components/layout': '@/components/layout',
    'components/core': '@/components/common',
    'components/common': '@/components/common',
    'components/navigation': '@/components/layout',
    'UI': '@/components/ui',
    'LAYOUT': '@/components/layout',
    'CORE': '@/components/common',

    // ASSETS
    'ASSETS/images': '@/assets/images',
    'ASSETS/IMAGES': '@/assets/images',
    'images': '@/assets/images',

    // STORE/CONTEXT
    'CONTEXT': '@/store',
    'context': '@/store',

    // SERVICES
    'SERVICES': '@/services',
    'services/apiClient': '@/services/api/axios.config',
    'services/api': '@/services/api/endpoints',
    'services/medicalService': '@/services/medical.service',
    'services/mriSegmentationService': '@/services/clinical.service',
    'services': '@/services',

    // UTILS
    'utils/formatters': '@/utils/formatters',
    'utils/validation': '@/utils/validators',
    'utils/securityUtils': '@/utils/helpers/security',
    'utils/verificationUtils': '@/utils/helpers/verification',
    'utils': '@/utils',

    // OTHERS
    'HOOKS': '@/hooks',
    'hooks': '@/hooks',
    'CONFIG': '@/config',
    'config': '@/config',
    'TYPES': '@/types',
    'types': '@/types',
    'STYLES': '@/styles',
    'styles': '@/styles',
    'PAGE': '@/pages',
    'pages': '@/pages',
};

function walk(dir) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        if (fs.statSync(fullPath).isDirectory()) {
            walk(fullPath);
        } else if (/\.(js|jsx|ts|tsx|css)$/.test(file)) {
            fixImports(fullPath);
        }
    }
}

function fixImports(filePath) {
    let content = fs.readFileSync(filePath, 'utf8');
    let originalContent = content;

    // Order mappings by specificity (descending length) to avoid greedy matches
    const sortedMappings = Object.entries(ALIAS_MAPPING).sort((a, b) => b[0].length - a[0].length);

    for (const [oldKey, newAlias] of sortedMappings) {
        // Escape dots and slashes
        // Match: './OLD_KEY/', '../OLD_KEY/', '../../OLD_KEY/', etc.
        const regex = new RegExp(`(['"])(\\.\\.?\\/)+${oldKey.replace(/\//g, '\\/')}(\\/|['"])`, 'g');
        content = content.replace(regex, (match, quote, dots, suffix) => {
            return `${quote}${newAlias}${suffix}`;
        });

        // Also match absolute src imports if any
        const regexAbs = new RegExp(`(['"])src\\/${oldKey.replace(/\//g, '\\/')}(\\/|['"])`, 'g');
        content = content.replace(regexAbs, (match, quote, suffix) => {
            return `${quote}${newAlias}${suffix}`;
        });
    }

    // Final cleanup: convert any remaining absolute src/ imports to @/
    content = content.replace(/(['"])src\//g, "$1@/");

    if (content !== originalContent) {
        fs.writeFileSync(filePath, content, 'utf8');
        console.log(`Professional Fix: ${filePath}`);
    }
}

console.log('Starting professional import normalization...');
walk(SRC_DIR);
console.log('Finished!');
