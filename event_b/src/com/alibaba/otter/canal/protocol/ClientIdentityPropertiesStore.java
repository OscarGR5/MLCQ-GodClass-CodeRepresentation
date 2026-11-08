package com.alibaba.otter.canal.protocol;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Objects;
import java.util.Properties;

/** Single-file properties persistence, kept separate from the client identity model. */
public final class ClientIdentityPropertiesStore {

    private ClientIdentityPropertiesStore() {}

    /**
     * Creates or replaces a file using standard Properties escaping. Null string fields
     * are omitted; empty strings are retained. Parent directories must already exist.
     * Replacement is not atomic. The supplied identity is not modified.
     *
     * @throws NullPointerException if path or identity is null
     * @throws IOException if the file cannot be written
     */
    public static void save(Path path, ClientIdentity identity) throws IOException {
        Objects.requireNonNull(path, "path");
        Objects.requireNonNull(identity, "identity");
        Properties properties = new Properties();
        if (identity.getDestination() != null) {
            properties.setProperty("destination", identity.getDestination());
        }
        properties.setProperty("clientId", Short.toString(identity.getClientId()));
        if (identity.getFilter() != null) {
            properties.setProperty("filter", identity.getFilter());
        }
        try (OutputStream output = Files.newOutputStream(path)) {
            properties.store(output, "Canal client identity");
        }
    }

    /**
     * Loads a new identity. Absent string keys mean null; clientId is required and
     * must parse as a short without trimming. Unknown keys are ignored.
     *
     * @throws NullPointerException if path is null
     * @throws IOException for filesystem errors, invalid escapes, or invalid/missing clientId
     */
    public static ClientIdentity load(Path path) throws IOException {
        Objects.requireNonNull(path, "path");
        Properties properties = new Properties();
        try (InputStream input = Files.newInputStream(path)) {
            properties.load(input);
        } catch (IllegalArgumentException invalidProperties) {
            throw new IOException("Invalid client identity properties", invalidProperties);
        }
        String clientId = properties.getProperty("clientId");
        if (clientId == null) {
            throw new IOException("Missing clientId property");
        }
        final short parsedClientId;
        try {
            parsedClientId = Short.parseShort(clientId);
        } catch (NumberFormatException invalidClientId) {
            throw new IOException("Invalid clientId property", invalidClientId);
        }
        return new ClientIdentity(properties.getProperty("destination"), parsedClientId,
                                  properties.getProperty("filter"));
    }
}
