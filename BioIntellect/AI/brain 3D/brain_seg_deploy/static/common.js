function parseNPY(buffer) {
    try {
        const magic = new TextDecoder("utf-8").decode(buffer.slice(0, 6));
        if (magic !== "\x93NUMPY") throw new Error("Not a valid NPY file");
        
        const version = new Uint8Array(buffer.slice(6, 8));
        const headerLength = version[0] === 1 ? 
            new DataView(buffer.slice(8, 10)).getUint16(0, true) :
            new DataView(buffer.slice(8, 12)).getUint32(0, true);
        
        const headerStr = new TextDecoder("utf-8").decode(buffer.slice(8 + (version[0] === 1 ? 2 : 4), 8 + (version[0] === 1 ? 2 : 4) + headerLength));
        
        // Parse header safely without eval
        const header = {};
        headerStr.replace(/'(\w+)':\s*([^,}]+)/g, (match, key, value) => {
            if (key === 'shape') {
                header.shape = value.replace(/\(|\)/g, '').split(',').filter(x => x.trim()).map(x => parseInt(x.trim()));
            } else if (key === 'descr') {
                header.descr = value.replace(/'/g, '').trim();
            } else if (key === 'fortran_order') {
                header.fortran_order = value.trim() === 'True';
            }
        });
        
        if (!header.shape || !header.descr) {
            throw new Error("Invalid NPY header");
        }
        
        const dataOffset = 8 + (version[0] === 1 ? 2 : 4) + headerLength;
        let data;
        
        if (header.descr === "<f4" || header.descr === "|f4") {
            data = new Float32Array(buffer, dataOffset);
        } else if (header.descr === "|u1" || header.descr === "<u1") {
            data = new Uint8Array(buffer, dataOffset);
        } else if (header.descr === "<i4" || header.descr === "|i4") {
            data = new Int32Array(buffer, dataOffset);
        } else {
            throw new Error(`Unsupported data type: ${header.descr}`);
        }
        
        return { shape: header.shape, data };
    } catch (error) {
        console.error("Failed to parse NPY:", error);
        return null;
    }
}
