const MAGIC = new Uint8Array([0x93, 0x4e, 0x55, 0x4d, 0x50, 0x59])

const DTYPE_CONSTRUCTORS = {
  '<f4': Float32Array,
  '|f4': Float32Array,
  '<f2': Uint16Array,
  '|u1': Uint8Array,
  '<u1': Uint8Array,
  '<i1': Int8Array,
  '<i2': Int16Array,
  '<u2': Uint16Array,
  '<i4': Int32Array,
  '<u4': Uint32Array,
}

const parseHeader = (headerText) => {
  const descr = /'descr':\s*'([^']+)'/.exec(headerText)?.[1]
  const fortranOrderText = /'fortran_order':\s*(True|False)/.exec(headerText)?.[1]
  const shapeText = /'shape':\s*\(([^)]*)\)/.exec(headerText)?.[1]

  if (!descr || !shapeText) {
    throw new Error('Invalid NumPy header.')
  }

  const shape = shapeText
    .split(',')
    .map((value) => value.trim())
    .filter(Boolean)
    .map((value) => Number.parseInt(value, 10))

  return {
    descr,
    fortranOrder: fortranOrderText === 'True',
    shape,
  }
}

export const parseNumpyFile = (buffer) => {
  const bytes = new Uint8Array(buffer, 0, MAGIC.length)
  for (let index = 0; index < MAGIC.length; index += 1) {
    if (bytes[index] !== MAGIC[index]) {
      throw new Error('Invalid NumPy file format.')
    }
  }

  const view = new DataView(buffer)
  let offset = MAGIC.length
  const majorVersion = view.getUint8(offset)
  offset += 1
  offset += 1

  const headerLength =
    majorVersion >= 2 ? view.getUint32(offset, true) : view.getUint16(offset, true)
  offset += majorVersion >= 2 ? 4 : 2

  const headerBytes = new Uint8Array(buffer, offset, headerLength)
  const headerText = new TextDecoder().decode(headerBytes)
  offset += headerLength

  const { descr, fortranOrder, shape } = parseHeader(headerText)
  if (fortranOrder) {
    throw new Error('Fortran-ordered NumPy arrays are not supported.')
  }

  const TypedArrayCtor = DTYPE_CONSTRUCTORS[descr]
  if (!TypedArrayCtor) {
    throw new Error(`Unsupported NumPy dtype: ${descr}`)
  }

  const elementCount = shape.reduce((total, value) => total * value, 1)
  const rawData = new TypedArrayCtor(buffer, offset, elementCount)
  const data = new TypedArrayCtor(rawData)

  return {
    data,
    shape,
    descr,
    fortranOrder,
  }
}

export default parseNumpyFile
