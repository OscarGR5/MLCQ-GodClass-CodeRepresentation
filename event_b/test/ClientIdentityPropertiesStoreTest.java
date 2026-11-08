import com.alibaba.otter.canal.protocol.ClientIdentity;
import com.alibaba.otter.canal.protocol.ClientIdentityPropertiesStore;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.Objects;
import java.util.Properties;

/** Uses real temporary files and explicitly checks destination, clientId AND filter. */
public final class ClientIdentityPropertiesStoreTest {
    private static int checks;

    public static void main(String[] args) throws Exception {
        Path directory = Files.createTempDirectory("event-b-identity-");
        try {
            run(directory);
        } finally {
            // Only the files created below belong to this test.
            try (java.nio.file.DirectoryStream<Path> files = Files.newDirectoryStream(directory)) {
                for (Path file : files) {
                    Files.delete(file);
                }
            }
            Files.delete(directory);
        }
        System.out.println("ALL " + checks + " CHECKS PASSED: client identity properties persistence.");
    }

    private static void run(final Path directory) throws Exception {
        final Path file = directory.resolve("identity.properties");
        roundTrip(file, "normal", "example", (short) 12, "db\\..*");
        roundTrip(file, "short minimum", "minimum", Short.MIN_VALUE, "filter-min");
        roundTrip(file, "short maximum", "maximum", Short.MAX_VALUE, "filter-max");
        roundTrip(file, "null strings", null, (short) 0, null);
        Properties properties = readProperties(file);
        check("null destination key omitted", false, properties.containsKey("destination"));
        check("null filter key omitted", false, properties.containsKey("filter"));
        check("zero clientId written", "0", properties.getProperty("clientId"));
        roundTrip(file, "empty strings", "", (short) -1, "");
        properties = readProperties(file);
        check("empty destination key present", "", properties.getProperty("destination"));
        check("empty filter key present", "", properties.getProperty("filter"));
        roundTrip(file, "null destination empty filter", null, (short) 7, "");
        roundTrip(file, "empty destination null filter", "", (short) 8, null);
        roundTrip(file, "escaped Unicode and whitespace", "  café:目的地=\\\n\t!#  ",
                  (short) 42, " \t db\\..*=a:b\n\r\f😀  ");

        ClientIdentity left = new ClientIdentity("same", (short) 1, "filter-A");
        ClientIdentity right = new ClientIdentity("same", (short) 1, "filter-B");
        check("baseline equals ignores filter", true, left.equals(right));
        ClientIdentityPropertiesStore.save(file, right);
        fields("filter must survive despite equals", ClientIdentityPropertiesStore.load(file),
               "same", (short) 1, "filter-B");
        fields("save does not mutate input", right, "same", (short) 1, "filter-B");

        write(file, "clientId=23\nextra=ignored\n");
        fields("optional keys absent", ClientIdentityPropertiesStore.load(file), null, (short) 23, null);
        write(file, "destination=external\nclientId=2\nfilter=old\nfilter=new\nextra=ignored\n");
        fields("standard properties duplicate and unknown keys", ClientIdentityPropertiesStore.load(file),
               "external", (short) 2, "new");

        // Saving a shorter/null-valued identity replaces rather than appends to the file.
        roundTrip(file, "overwrite removes stale fields", null, (short) 3, null);
        check("only clientId key remains", 1, readProperties(file).size());

        final byte[] before = Files.readAllBytes(file);
        expect("null identity", NullPointerException.class, new Operation() {
            public void run() throws Exception { ClientIdentityPropertiesStore.save(file, null); }
        });
        check("null identity did not truncate file", true, Arrays.equals(before, Files.readAllBytes(file)));
        expect("null save path", NullPointerException.class, new Operation() {
            public void run() throws Exception { ClientIdentityPropertiesStore.save(null, left); }
        });
        expect("null load path", NullPointerException.class, new Operation() {
            public void run() throws Exception { ClientIdentityPropertiesStore.load(null); }
        });
        expect("missing file", IOException.class, new Operation() {
            public void run() throws Exception { ClientIdentityPropertiesStore.load(directory.resolve("missing")); }
        });
        expect("missing parent", IOException.class, new Operation() {
            public void run() throws Exception {
                ClientIdentityPropertiesStore.save(directory.resolve("missing/identity.properties"), left);
            }
        });
        expect("cannot write directory", IOException.class, new Operation() {
            public void run() throws Exception { ClientIdentityPropertiesStore.save(directory, left); }
        });
        expect("cannot read directory as properties", IOException.class, new Operation() {
            public void run() throws Exception { ClientIdentityPropertiesStore.load(directory); }
        });

        invalid(file, "missing clientId", "destination=x\nfilter=y\n", null);
        invalid(file, "empty clientId", "clientId=\n", NumberFormatException.class);
        invalid(file, "nonnumeric clientId", "clientId=abc\n", NumberFormatException.class);
        invalid(file, "clientId overflow", "clientId=32768\n", NumberFormatException.class);
        invalid(file, "clientId underflow", "clientId=-32769\n", NumberFormatException.class);
        // Leading unescaped spaces are stripped by Properties itself. Escaped spaces remain values.
        invalid(file, "escaped leading space in clientId", "clientId=\\ 1\n", NumberFormatException.class);
        invalid(file, "trailing space in clientId", "clientId=1 \n", NumberFormatException.class);
        invalid(file, "malformed Unicode escape", "clientId=1\nfilter=\\uZZZZ\n", IllegalArgumentException.class);

        // A successfully reopened and replaced malformed file also exercises the error cleanup path.
        roundTrip(file, "recovery after malformed input", "recovered", (short) 9, "all-three-fields");
    }

    private static void roundTrip(Path file, String name, String destination, short clientId,
                                  String filter) throws IOException {
        ClientIdentity original = new ClientIdentity(destination, clientId, filter);
        ClientIdentityPropertiesStore.save(file, original);
        ClientIdentity loaded = ClientIdentityPropertiesStore.load(file);
        fields(name, loaded, destination, clientId, filter);
        check(name + " returns a new instance", false, original == loaded);
    }

    private static void fields(String name, ClientIdentity actual, String destination, short clientId,
                               String filter) {
        check(name + " destination", destination, actual.getDestination());
        check(name + " clientId", clientId, actual.getClientId());
        check(name + " filter", filter, actual.getFilter());
    }

    private static void invalid(final Path file, String name, String content,
                                Class<? extends Throwable> cause) throws Exception {
        write(file, content);
        Throwable error = expect(name, IOException.class, new Operation() {
            public void run() throws Exception { ClientIdentityPropertiesStore.load(file); }
        });
        if (cause != null) {
            check(name + " cause", true, cause.isInstance(error.getCause()));
        }
    }

    private static Properties readProperties(Path file) throws IOException {
        Properties properties = new Properties();
        try (InputStream input = Files.newInputStream(file)) {
            properties.load(input);
        }
        return properties;
    }

    private static void write(Path file, String content) throws IOException {
        Files.write(file, content.getBytes(StandardCharsets.ISO_8859_1));
    }

    private static Throwable expect(String name, Class<? extends Throwable> type, Operation operation)
            throws Exception {
        try {
            operation.run();
        } catch (Exception error) {
            if (!type.isInstance(error)) {
                throw new AssertionError(name + ": expected " + type.getSimpleName(), error);
            }
            checks++;
            System.out.println("ok  " + name + " -> " + type.getSimpleName());
            return error;
        }
        throw new AssertionError(name + ": expected " + type.getSimpleName());
    }

    private static void check(String name, Object expected, Object actual) {
        if (!Objects.equals(expected, actual)) {
            throw new AssertionError(name + ": expected " + expected + ", got " + actual);
        }
        checks++;
        System.out.println("ok  " + name);
    }

    private interface Operation {
        void run() throws Exception;
    }
}
