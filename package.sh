#!/bin/bash
# Package creation script for Oracle FOCUS Agent

VERSION="1.0.0"
PACKAGE_NAME="agent-oci-to-umbrella-${VERSION}"
PACKAGE_DIR="${PACKAGE_NAME}"

echo "Creating deployment package: ${PACKAGE_NAME}"
echo ""

# Create package directory
mkdir -p ${PACKAGE_DIR}

# Copy distribution files
echo "Copying distribution files..."
cp -r dist ${PACKAGE_DIR}/

# Copy systemd service
echo "Copying systemd service..."
cp -r systemd ${PACKAGE_DIR}/

# Copy installation script
echo "Copying installation script..."
cp install.sh ${PACKAGE_DIR}/
chmod +x ${PACKAGE_DIR}/install.sh

# Copy configuration template
echo "Copying configuration template..."
cp config.template.yaml ${PACKAGE_DIR}/

# Copy documentation
echo "Copying documentation..."
cp README.md ${PACKAGE_DIR}/
cp INSTALL.md ${PACKAGE_DIR}/
cp QUICKSTART.md ${PACKAGE_DIR}/
cp REQUIREMENTS.md ${PACKAGE_DIR}/
cp INSTALLATION_GUIDE.html ${PACKAGE_DIR}/

# Create tarball
echo ""
echo "Creating tarball..."
tar -czf ${PACKAGE_NAME}.tar.gz ${PACKAGE_DIR}

# Calculate checksum
echo "Calculating checksum..."
sha256sum ${PACKAGE_NAME}.tar.gz > ${PACKAGE_NAME}.tar.gz.sha256

# Clean up temporary directory
rm -rf ${PACKAGE_DIR}

# Show results
echo ""
echo "=================================================="
echo "Package created successfully!"
echo "=================================================="
echo ""
echo "Package: ${PACKAGE_NAME}.tar.gz"
echo "Size: $(du -h ${PACKAGE_NAME}.tar.gz | cut -f1)"
echo "SHA256: $(cat ${PACKAGE_NAME}.tar.gz.sha256 | cut -d' ' -f1)"
echo ""
echo "To install on a Linux machine:"
echo "1. Transfer the tarball to the target machine"
echo "2. Extract: tar -xzf ${PACKAGE_NAME}.tar.gz"
echo "3. Change directory: cd ${PACKAGE_NAME}"
echo "4. Run installer: sudo ./install.sh"
echo ""
echo "=================================================="
